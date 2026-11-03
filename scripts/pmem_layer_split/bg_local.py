# -*- coding: utf-8 -*-
"""Build background by digging foreground footprints out of the original ref."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from .job import Job

# Large digs have no context for Telea / heavy blur → smear. Use flat fill instead.
_MAX_DIG_FRAC_FOR_INPAINT = 0.28


def build_local_background(
    job: Job,
    *,
    feather: int = 2,
    out_name: str | None = None,
    skip_ids: set[str] | None = None,
    inpaint_radius: int = 3,
    force_inpaint: bool = False,
) -> Path:
    """Write new/<bg_file> from ref with non-bg footprints cleared.

    - dig_frac ≤ 28%: Telea inpaint (sharp, enough context)
    - dig_frac > 28% (typical full-scene split): **flat median fill** of dug
      pixels from remaining undug scenery — keeps undug flowers/sky sharp,
      removes subjects under layers (no double ghosts), no Gaussian mud / stretch
    """
    truth = job.load_truth()
    ref = job.open_ref({"ref": truth.get("ref")})
    W, H = ref.size
    arr = np.array(ref.convert("RGBA"))
    skip_ids = skip_ids or set()

    bg_layer = next(
        (L for L in truth["layers"] if L["id"] == "bg" or L.get("fill") == "cover"),
        None,
    )
    if bg_layer is None:
        bg_layer = sorted(truth["layers"], key=lambda x: x.get("z", 0))[0]

    mask = np.zeros((H, W), dtype=np.float32)
    for L in truth["layers"]:
        if L["id"] == bg_layer["id"] or L["id"] in skip_ids:
            continue
        x0 = int(L["left"] * W)
        y0 = int(L["top"] * H)
        x1 = int((L["left"] + L["width"]) * W)
        y1 = int((L["top"] + L["height"]) * H)
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W, x1), min(H, y1)
        if x1 <= x0 or y1 <= y0:
            continue
        mask[y0:y1, x0:x1] = 1.0

    if feather > 0:
        mimg = Image.fromarray((mask * 255).astype(np.uint8), "L")
        mimg = mimg.filter(ImageFilter.GaussianBlur(feather))
        mask = np.array(mimg).astype(np.float32) / 255.0

    dug = mask > 0.4
    dig_frac = float(dug.mean()) if dug.size else 0.0
    fill_method = "none"
    rgb = arr[:, :, :3].copy()

    if dug.any():
        use_inpaint = force_inpaint or dig_frac <= _MAX_DIG_FRAC_FOR_INPAINT
        if use_inpaint:
            try:
                import cv2

                mask_u8 = (dug.astype(np.uint8) * 255)
                bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
                k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                mask_u8 = cv2.dilate(mask_u8, k, iterations=1)
                out_bgr = cv2.inpaint(bgr, mask_u8, inpaint_radius, cv2.INPAINT_TELEA)
                rgb = cv2.cvtColor(out_bgr, cv2.COLOR_BGR2RGB)
                fill_method = "inpaint"
            except Exception as exc:  # noqa: BLE001
                print("cv2 inpaint failed, flat fill:", exc)
                use_inpaint = False

        if not use_inpaint or fill_method != "inpaint":
            # Flat fill from undug median — sharp elsewhere, no smear, no doubles
            undug = ~dug
            if undug.any():
                fill_rgb = np.median(rgb[undug], axis=0).astype(np.uint8)
            else:
                fill_rgb = np.array([120, 160, 90], dtype=np.uint8)
            # Soft edge: blend fill with original near dig boundary
            soft = mask[..., None]
            fill_img = np.broadcast_to(fill_rgb, rgb.shape).astype(np.float32)
            rgb_f = rgb.astype(np.float32)
            rgb = np.clip(rgb_f * (1.0 - soft) + fill_img * soft, 0, 255).astype(np.uint8)
            fill_method = "flat_median"
            print(
                f"bg dig_frac={dig_frac:.2f} → flat_median fill "
                f"(skip smear inpaint)"
            )

        arr[:, :, :3] = rgb
        arr[:, :, 3] = 255

    out = Image.fromarray(arr, "RGBA")
    job.new_dir.mkdir(exist_ok=True)
    fname = out_name or bg_layer.get("file") or "bg.png"
    dest = job.new_dir / fname
    out.save(dest)

    status = job.load_status()
    status.setdefault("layers", {})[bg_layer["id"]] = {
        "status": "ok",
        "source": "local_dig",
        "file": f"new/{fname}",
        "retries": 0,
        "fill_method": fill_method,
        "dig_frac": round(dig_frac, 4),
    }
    job.save_status(status)
    print("wrote local bg", dest, f"method={fill_method}")
    return dest
