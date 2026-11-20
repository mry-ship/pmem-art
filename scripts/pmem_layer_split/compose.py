# -*- coding: utf-8 -*-
"""Contain / cover / width compose into calibrated footprints."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .job import Job


def trim_alpha(im: Image.Image) -> Image.Image:
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def cover_resize(
    im: Image.Image,
    W: int,
    H: int,
    *,
    ref_rgb: np.ndarray | None = None,
    sky_frac: float = 0.32,
) -> Image.Image:
    """Uniform scale + crop to WxH. Never non-uniform stretch (no squash).

    When ref_rgb is provided and the scaled sprite is larger than the canvas,
    search crop offset to minimize sky-band MAE vs ref (locks moon/horizon drift
    on ultra-tall/wide aspect mismatches). Falls back to center crop.
    """
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    iw, ih = im.size
    scale = max(W / max(1, iw), H / max(1, ih))
    nw, nh = max(1, int(round(iw * scale))), max(1, int(round(ih * scale)))
    _lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
    r = im.resize((nw, nh), _lanczos)
    left = max(0, (nw - W) // 2)
    top = max(0, (nh - H) // 2)
    if ref_rgb is not None and ref_rgb.shape[0] == H and ref_rgb.shape[1] == W:
        sky_h = max(8, int(H * sky_frac))
        ref_sky = ref_rgb[:sky_h].astype(np.float32)
        best = None
        # coarse then fine search on leftover margins
        x_range = range(0, max(1, nw - W + 1))
        y_range = range(0, max(1, nh - H + 1))
        step = 4 if max(nw - W, nh - H) > 24 else 1
        for y0 in list(y_range)[::step] or [0]:
            for x0 in list(x_range)[::step] or [0]:
                patch = np.asarray(r.crop((x0, y0, x0 + W, y0 + H)).convert("RGB"), dtype=np.float32)
                mae = float(np.abs(patch[:sky_h] - ref_sky).mean())
                if best is None or mae < best[0]:
                    best = (mae, x0, y0)
        if best is not None:
            # refine ±step around best
            bx, by = best[1], best[2]
            for y0 in range(max(0, by - step), min(nh - H + 1, by + step + 1)):
                for x0 in range(max(0, bx - step), min(nw - W + 1, bx + step + 1)):
                    patch = np.asarray(
                        r.crop((x0, y0, x0 + W, y0 + H)).convert("RGB"), dtype=np.float32
                    )
                    mae = float(np.abs(patch[:sky_h] - ref_sky).mean())
                    if mae < best[0]:
                        best = (mae, x0, y0)
            left, top = best[1], best[2]
            print(f"bg cover sky-align mae={best[0]:.2f} offset=({left},{top}) center=({(nw-W)//2},{(nh-H)//2})")
    return r.crop((left, top, left + W, top + H))


def _anchor_xy(L: int, T: int, BW: int, BH: int, nw: int, nh: int, anchor: str) -> tuple[int, int]:
    x = L + (BW - nw) // 2
    a = (anchor or "bottom-center").lower().replace("_", "-")
    if a in ("center", "middle", "mid"):
        y = T + (BH - nh) // 2
    elif a in ("top-center", "top", "hang", "ceiling"):
        y = T
    else:
        y = T + BH - nh
    return x, y


def autofit_scale_to_ref(
    ref_rgb: np.ndarray,
    sprite_rgba: Image.Image,
    L: int,
    T: int,
    BW: int,
    BH: int,
    *,
    anchor: str = "bottom-center",
    base_mode: str = "contain",
    scales: tuple[float, ...] = (1.0, 0.92, 0.85, 0.78, 0.72, 0.66),
) -> float:
    """Pick scale factor ≤ contain-fit that best matches the ref crop region (NCC).

    Locks absolute size toward the original scene when the isolate engine zoomed in.
    """
    if BW < 4 or BH < 4:
        return 1.0
    H, W = ref_rgb.shape[:2]
    x1, y1 = min(W, L + BW), min(H, T + BH)
    L, T = max(0, L), max(0, T)
    patch = ref_rgb[T:y1, L:x1]
    if patch.size < 16:
        return 1.0
    iw, ih = sprite_rgba.size
    if base_mode == "width":
        base = BW / max(1, iw)
    elif base_mode == "height":
        base = BH / max(1, ih)
    else:
        base = min(BW / max(1, iw), BH / max(1, ih))
    _lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
    best_s, best_score = 1.0, -1e9
    patch_l = patch.astype(np.float32).mean(axis=2)
    patch_l = patch_l - patch_l.mean()
    pnorm = float(np.linalg.norm(patch_l)) + 1e-6
    for s in scales:
        nw = max(1, int(iw * base * s))
        nh = max(1, int(ih * base * s))
        if nw > BW or nh > BH:
            continue
        r = sprite_rgba.resize((nw, nh), _lanczos)
        x, y = _anchor_xy(L, T, BW, BH, nw, nh, anchor)
        # composite sprite luma into zeros then compare under alpha
        canvas = np.zeros((BH, BW), dtype=np.float32)
        weight = np.zeros((BH, BW), dtype=np.float32)
        arr = np.asarray(r)
        a = arr[:, :, 3].astype(np.float32) / 255.0
        lum = arr[:, :, :3].astype(np.float32).mean(axis=2)
        rx0, ry0 = x - L, y - T
        rx1, ry1 = rx0 + nw, ry0 + nh
        if rx0 < 0 or ry0 < 0 or rx1 > BW or ry1 > BH:
            continue
        canvas[ry0:ry1, rx0:rx1] = lum * a
        weight[ry0:ry1, rx0:rx1] = a
        # compare only where sprite has alpha; use patch under same ROI
        if weight.sum() < 8:
            continue
        # resize patch to BH,BW already is box size
        if patch_l.shape[0] != BH or patch_l.shape[1] != BW:
            continue
        mask = weight > 0.2
        if int(mask.sum()) < 16:
            continue
        a_v = canvas[mask]
        b_v = patch.astype(np.float32).mean(axis=2)[mask]
        a_v = a_v - a_v.mean()
        b_v = b_v - b_v.mean()
        denom = float(np.linalg.norm(a_v) * np.linalg.norm(b_v)) + 1e-6
        score = float((a_v * b_v).sum() / denom)
        if score > best_score:
            best_score = score
            best_s = s
    return float(best_s)


def place_scaled(
    canvas: Image.Image,
    im: Image.Image,
    L: int,
    T: int,
    BW: int,
    BH: int,
    mode: str = "contain",
    *,
    anchor: str = "bottom-center",
    pad: int = 500,
    scale_mul: float = 1.0,
) -> dict:
    """Place sprite into footprint box.

    anchor:
      - bottom-center: grounded props (default) — feet/base on box bottom
      - center: wall/ceiling props — keep in middle of truth box (position lock)
      - top-center: hanging fixtures
    scale_mul: extra factor ≤1 from autofit_scale_to_ref (size lock)
    """
    W, H = canvas.size
    iw, ih = im.size
    if mode == "height":
        scale = BH / ih
    elif mode == "width":
        scale = BW / iw
    elif mode == "cover":
        scale = max(BW / iw, BH / ih)
    else:
        scale = min(BW / iw, BH / ih)
    scale *= max(0.5, min(1.0, float(scale_mul)))
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    _lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
    r = im.resize((nw, nh), _lanczos)
    a = (anchor or "bottom-center").lower().replace("_", "-")
    x, y = _anchor_xy(L, T, BW, BH, nw, nh, a)
    tmp = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
    tmp.paste(r, (x + pad, y + pad), r)
    canvas.alpha_composite(tmp.crop((pad, pad, pad + W, pad + H)))
    return {
        "left": x / W,
        "top": y / H,
        "width": nw / W,
        "height": nh / H,
        "nw": nw,
        "nh": nh,
        "box_w": BW,
        "box_h": BH,
        "anchor": a,
        "scale_mul": round(float(scale_mul), 4),
    }


def resolve_sprite(job: Job, layer: dict) -> Path | None:
    name = layer["file"]
    candidates = [
        job.new_dir / name,
        job.new_dir / Path(name).name,
        job.root / "new" / Path(name).name,
        job.root / name,
    ]
    # also try id.png
    candidates.append(job.new_dir / f"{layer['id']}.png")
    for p in candidates:
        if p.exists():
            return p
    return None


def compose(job: Job, *, scale: int = 2) -> dict:
    truth = job.load_truth()
    cw = int(truth["canvas"]["w"])
    ch = int(truth["canvas"]["h"])
    W, H = cw * scale, ch * scale
    job.trim_dir.mkdir(exist_ok=True)
    job.new_dir.mkdir(exist_ok=True)

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    placed = []
    metrics = {}
    _lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
    ref_full = job.open_ref({"ref": truth.get("ref")}).resize((W, H), _lanczos)
    ref_rgb = np.asarray(ref_full.convert("RGB"))
    try:
        plan = job.load_plan()
    except Exception:
        plan = {}
    compose_opts = plan.get("compose") if isinstance(plan.get("compose"), dict) else {}
    plan_no_autofit = plan.get("no_autofit") is True or compose_opts.get("autofit") is False

    for layer in sorted(truth["layers"], key=lambda x: x.get("z", 0)):
        src = resolve_sprite(job, layer)
        if src is None:
            print("MISSING", layer["id"], layer["file"])
            metrics[layer["id"]] = {"missing": True}
            continue
        im = Image.open(src)
        mode = layer.get("fill", "contain")
        if layer["id"] == "bg":
            # Skill: 禁止非等比拉伸. Engine size (e.g. 1024x1536) rarely matches
            # ultra-tall/wide refs — uniform cover + sky-aligned crop locks moon/horizon.
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            r = cover_resize(im, W, H, ref_rgb=ref_rgb)
            canvas.alpha_composite(r)
            r.save(job.trim_dir / Path(layer["file"]).name)
            info = {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}
            box_asp = W / max(1, H)
            spr_asp = im.size[0] / max(1, im.size[1])
            fill = 1.0
            stretch_err = abs(spr_asp - box_asp) / max(spr_asp, box_asp, 1e-6)
            metrics[layer["id"]] = {
                "box_px_asp": round(box_asp, 4),
                "spr_asp": round(spr_asp, 4),
                "fill": 1.0,
                "scale_mul": 1.0,
                "mode": "cover_uniform_sky_align",
                "stretch_err": round(stretch_err, 4),
            }
            print(
                f"bg: cover_uniform_sky_align from {src.name} "
                f"src_asp={spr_asp:.3f} canvas_asp={box_asp:.3f} stretch_err={stretch_err:.3f}"
            )
        else:
            im = trim_alpha(im.convert("RGBA"))
            im.save(job.trim_dir / Path(layer["file"]).name)
            # Prefer frozen pixel box from truth/footprints (position+size lock)
            if layer.get("px") and len(layer["px"]) == 4:
                x0, y0, x1, y1 = [int(v) for v in layer["px"]]
                # truth px is in ref canvas coords; scale to compose canvas
                ref_w = max(1, int(truth["canvas"]["w"]))
                ref_h = max(1, int(truth["canvas"]["h"]))
                sx, sy = W / ref_w, H / ref_h
                L = int(x0 * sx)
                T = int(y0 * sy)
                BW = max(1, int((x1 - x0) * sx))
                BH = max(1, int((y1 - y0) * sy))
            else:
                L = int(layer["left"] * W)
                T = int(layer["top"] * H)
                BW = int(layer["width"] * W)
                BH = int(layer["height"] * H)
            if mode == "cover" and layer["id"] != "bg":
                mode = "contain"  # skill: forbid prop cover
            # Position lock: wall/ceiling (ungrounded) → center in truth box;
            # grounded → bottom-align. Explicit layer.anchor wins.
            if layer.get("anchor"):
                anchor = str(layer.get("anchor"))
            elif layer.get("grounded") is False:
                anchor = "center"
            else:
                anchor = "bottom-center"
            # Size lock: shrink ≤ contain if a smaller scale matches the original crop better.
            # Job/plan can force full footprint fit: compose.autofit=false or no_autofit=true
            if plan_no_autofit or layer.get("no_autofit") is True:
                scale_mul = 1.0
            else:
                scale_mul = autofit_scale_to_ref(
                    ref_rgb, im, L, T, BW, BH, anchor=anchor, base_mode=mode
                )
            info = place_scaled(
                canvas, im, L, T, BW, BH, mode, anchor=anchor, scale_mul=scale_mul
            )
            box_asp = BW / BH if BH else 1.0
            spr_asp = im.size[0] / max(1, im.size[1])
            fill = (info["nw"] * info["nh"]) / max(1, BW * BH)
            print(
                f"{layer['id']}: {mode}/{anchor} fill={fill:.2f} "
                f"scale_mul={scale_mul:.2f} box_px={box_asp:.2f} spr={spr_asp:.2f} src={src.name}"
            )

            metrics[layer["id"]] = {
                "box_px_asp": round(box_asp, 4),
                "spr_asp": round(spr_asp, 4),
                "fill": round(fill, 4),
                "scale_mul": round(float(scale_mul), 4),
                "mode": mode if layer["id"] != "bg" else "cover",
            }
        placed.append(
            {
                "id": layer["id"],
                "name": layer.get("name", layer["id"]),
                "note": layer.get("note", ""),
                "z": layer.get("z", 0),
                "file": f"new_trim/{Path(layer['file']).name}",
                "truth": {
                    "left": layer["left"],
                    "top": layer["top"],
                    "width": layer["width"],
                    "height": layer["height"],
                },
                "left": info["left"],
                "top": info["top"],
                "width": info["width"],
                "height": info["height"],
            }
        )

    from .job import save_json

    save_json(job.placements_path, placed)
    save_json(job.root / "_compose_metrics.json", metrics)

    ref = job.open_ref({"ref": truth.get("ref")}).resize((W, H), Image.Resampling.LANCZOS)
    blend = Image.blend(ref, canvas, 0.45)
    board = Image.new("RGB", (W * 3 + 40, H + 20), (30, 36, 44))
    board.paste(ref.convert("RGB"), (10, 10))
    board.paste(canvas.convert("RGB"), (W + 20, 10))
    board.paste(blend.convert("RGB"), (W * 2 + 30, 10))
    out = job.root / "_compose_preview.png"
    board.save(out)
    canvas.convert("RGB").save(job.root / "_compose_mid.png")
    print("wrote", out)
    return {"placed": placed, "metrics": metrics, "canvas": (W, H)}
