# -*- coding: utf-8 -*-
"""Post-isolate normalization shared by all layer-split jobs.

After engine isolate:
1) Crop/pad bg plate to canvas aspect (never squash) — engine 1024x1536 vs tall/wide refs.
2) Props: if the file is still the engine frame, cut only the empty part of the
   known pad bars. A thin tip that spilled into a bar is kept. Do not crop
   to the alpha bbox. Then letterbox that picture band to the footprint aspect.
   A second run sees the footprint aspect and does not cut again.

These steps are skill contract — not job-specific hacks.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from .compose import resolve_sprite
from .defaults import GATE, engine_content_band
from .job import Job


def _letterbox_keep_frame(im: Image.Image, target_asp: float) -> tuple[Image.Image, int, int]:
    """Pad the full frame to the footprint aspect. Returns (image, dx, dy).

    Do not crop to the alpha bbox. Cropping recenters the subject and
    throws away where it sat inside the crop. dx/dy is the pad added on
    the left and top, so a picture-band rectangle can be shifted with it.
    """
    if im.mode != "RGBA":
        im = im.convert("RGBA")
    w, h = im.size
    cur = w / max(1, h)
    if abs(cur - target_asp) < 1e-3:
        return im, 0, 0
    if cur > target_asp:
        nh = max(h, int(round(w / target_asp)))
        canvas = Image.new("RGBA", (w, nh), (0, 0, 0, 0))
        dy = (nh - h) // 2
        canvas.paste(im, (0, dy), im)
        return canvas, 0, dy
    nw = max(w, int(round(h * target_asp)))
    canvas = Image.new("RGBA", (nw, h), (0, 0, 0, 0))
    dx = (nw - w) // 2
    canvas.paste(im, (dx, 0), im)
    return canvas, dx, 0


def normalize_bg_to_canvas_aspect(job: Job) -> Path | None:
    """Crop engine-wide/tall bg into canvas aspect band; resize to canvas px. Never squash content."""
    truth = job.load_truth()
    bg = next((L for L in truth["layers"] if L.get("id") == "bg"), None)
    if bg is None:
        return None
    src = resolve_sprite(job, bg)
    if src is None or not src.exists():
        return None
    cw = int(truth["canvas"]["w"])
    ch = int(truth["canvas"]["h"])
    target_asp = cw / max(1, ch)
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    cur = w / max(1, h)
    rel = abs(cur - target_asp) / max(cur, target_asp, 1e-6)
    if rel < 0.04 and abs(w - cw) < 2 and abs(h - ch) < 2:
        print(f"bg aspect ok {w}x{h} ≈ canvas {cw}x{ch}")
        return src
    if cur > target_asp:
        # wider than canvas → keep height, crop width (pillarbox removal)
        need_w = max(1, int(round(h * target_asp)))
        x0 = max(0, (w - need_w) // 2)
        im = im.crop((x0, 0, x0 + need_w, h))
    else:
        # taller than canvas → keep width, crop height (letterbox removal)
        need_h = max(1, int(round(w / target_asp)))
        y0 = max(0, (h - need_h) // 2)
        im = im.crop((0, y0, w, y0 + need_h))
    im = im.resize((cw, ch), Image.Resampling.LANCZOS)
    out = job.new_dir / Path(bg["file"]).name
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print(f"bg normalized {src.name} → {out.name} {im.size} asp={im.size[0]/im.size[1]:.3f}")
    return out


def _engine_wh(size: str) -> tuple[int, int] | None:
    try:
        ew, eh = [int(x) for x in str(size).lower().split("x")]
    except Exception:
        return None
    if ew < 8 or eh < 8:
        return None
    return ew, eh


def _strip_opaque_frac(im: Image.Image, box: tuple[int, int, int, int]) -> float:
    x0, y0, x1, y1 = box
    if x1 - x0 < 2 or y1 - y0 < 2:
        return 0.0
    alpha = im.getchannel("A").crop((x0, y0, x1, y1))
    hist = alpha.histogram()
    total = sum(hist)
    if total <= 0:
        return 0.0
    opaque = sum(hist[41:])
    return opaque / total


def _unpad_engine_band(
    im: Image.Image,
    band: tuple[float, float, float, float],
    bleed_max: float,
) -> tuple[Image.Image, bool, tuple[int, int, int, int]]:
    """Cut only the empty part of a known pad.

    Returns the image, whether a real share of the subject sits outside the
    picture band, and that band as a pixel box in the returned image.
    A thin tip that crosses the band line is kept (plus a 2px halo). The band
    box stays put, so compose can map the crop onto the footprint even when a
    tip hangs outside it. A full bar used to abort and keep the engine canvas;
    contain-fitting that canvas then shrunk the subject.
    """
    left, top, right, bottom = band
    w, h = im.size
    if max(band) < 0.01:
        return im, False, (0, 0, w, h)
    x0 = int(round(left * w))
    y0 = int(round(top * h))
    x1 = int(round((1.0 - right) * w))
    y1 = int(round((1.0 - bottom) * h))
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(w, max(x0 + 1, x1)), min(h, max(y0 + 1, y1))
    opaque = np.asarray(im.getchannel("A")) > 40
    inside = int(opaque[y0:y1, x0:x1].sum())
    outside = int(opaque.sum()) - inside
    outside_frac = outside / max(1, inside + outside)
    bled = outside_frac > float(bleed_max)
    keep_l, keep_t, keep_r, keep_b = x0, y0, x1, y1
    if x0 > 2 and opaque[:, :x0].any():
        cols = np.where(opaque[:, :x0].any(axis=0))[0]
        keep_l = max(0, int(cols.min()) - 2)
    if w - x1 > 2 and opaque[:, x1:].any():
        cols = np.where(opaque[:, x1:].any(axis=0))[0]
        keep_r = min(w, x1 + int(cols.max()) + 3)
    if y0 > 2 and opaque[:y0, :].any():
        rows = np.where(opaque[:y0, :].any(axis=1))[0]
        keep_t = max(0, int(rows.min()) - 2)
    if h - y1 > 2 and opaque[y1:, :].any():
        rows = np.where(opaque[y1:, :].any(axis=1))[0]
        keep_b = min(h, y1 + int(rows.max()) + 3)
    cropped = im.crop((keep_l, keep_t, keep_r, keep_b))
    band_box = (x0 - keep_l, y0 - keep_t, x1 - keep_l, y1 - keep_t)
    return cropped, bled, band_box


def letterbox_props_to_footprints(job: Job, *, ids: list[str] | None = None) -> list[str]:
    """Cut known engine bars, then letterbox the picture band to the footprint.

    Does not crop to the alpha bbox. A file that is already footprint-shaped
    is left on that path so a second normalize cannot cut the subject.
    """
    truth = job.load_truth()
    done = []
    fit_path = job.root / "_engine_fit.json"
    fit: dict = {}
    if fit_path.is_file():
        try:
            fit = json.loads(fit_path.read_text(encoding="utf-8"))
        except Exception:
            fit = {}
    bleed_max = float(GATE.get("engine_band_bleed_max", 0.08))
    for layer in truth["layers"]:
        lid = layer["id"]
        if lid == "bg":
            continue
        if ids is not None and lid not in ids:
            continue
        px = layer.get("px")
        if not px or len(px) != 4:
            continue
        L, T, R, B = [int(v) for v in px]
        box_asp = (R - L) / max(1, (B - T))
        src = resolve_sprite(job, layer)
        if src is None or not src.exists():
            continue
        im = Image.open(src).convert("RGBA")
        eng = _engine_wh(str(layer.get("size") or ""))
        crop_path = job.crops_dir / f"{lid}.png"
        on_engine = False
        if eng and crop_path.is_file():
            ew, eh = eng
            cur = im.size[0] / max(1, im.size[1])
            engine_asp = ew / max(1, eh)
            on_engine = abs(cur - engine_asp) / max(engine_asp, 1e-6) < 0.04
        if not on_engine:
            # Already the footprint frame. A second pass must not treat the
            # whole file as a new band and wipe the crop rectangle.
            prev = fit.get(lid) if isinstance(fit.get(lid), dict) else {}
            if "placed_band" not in prev:
                fit[lid] = {**prev, "bled": False, "placed_band": [0, 0, 0, 0]}
            continue
        with Image.open(crop_path) as crop:
            band = engine_content_band(crop.size[0], crop.size[1], ew, eh)
        im, bled, band_box = _unpad_engine_band(im, band, bleed_max)
        print(
            f"engine-band {lid} bled={bled} "
            f"bars LTRB={[round(v, 3) for v in band]} band_box={band_box}"
        )
        bx0, by0, bx1, by1 = band_box
        # Spill hangs outside the picture band. Pad would change which rectangle
        # is the crop. Keep the band box and let compose map that box onto the
        # footprint. Letterbox only when the band already is the whole file.
        spans_file = bx0 <= 1 and by0 <= 1 and bx1 >= im.size[0] - 1 and by1 >= im.size[1] - 1
        if spans_file:
            # The band is the whole picture. Letterbox pads are part of the
            # footprint frame, not overhang, so the saved file maps 1:1.
            out_im, _dx, _dy = _letterbox_keep_frame(im, box_asp)
            placed_band = [0, 0, 0, 0]
        else:
            out_im = im
            ow, oh = out_im.size
            placed_band = [
                round(bx0 / max(1, ow), 4),
                round(by0 / max(1, oh), 4),
                round((ow - bx1) / max(1, ow), 4),
                round((oh - by1) / max(1, oh), 4),
            ]
        fit[lid] = {
            "bled": bled,
            "band": [round(v, 4) for v in band],
            "placed_band": placed_band,
        }
        dst = job.new_dir / Path(layer["file"]).name
        out_im.save(dst)
        done.append(lid)
        print(
            f"letterbox {lid} → {dst.name} {out_im.size} "
            f"asp={out_im.size[0]/out_im.size[1]:.3f} box={box_asp:.3f}"
        )
    if fit:
        fit_path.write_text(json.dumps(fit, ensure_ascii=False, indent=2), encoding="utf-8")
    return done


def post_isolate_normalize(job: Job, *, ids: list[str] | None = None) -> dict:
    """Run after isolate / before compose. Safe to call repeatedly."""
    bg = normalize_bg_to_canvas_aspect(job)
    props = letterbox_props_to_footprints(job, ids=ids)
    return {"bg": str(bg) if bg else None, "letterboxed": props}
