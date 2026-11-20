# -*- coding: utf-8 -*-
"""Post-isolate normalization shared by all layer-split jobs.

After engine isolate:
1) Crop/pad bg plate to canvas aspect (never squash) — engine 1024x1536 vs tall/wide refs.
2) Letterbox prop sprites to frozen footprint aspect (alpha=1 pad) so asp_err/fill can pass
   without widening footprints; compose.autofit then shrinks to match ref.

These steps are skill contract — not job-specific hacks.
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

from .compose import resolve_sprite
from .job import Job


def _letterbox_keep_trim(im: Image.Image, target_asp: float) -> Image.Image:
    bb = im.getchannel("A").getbbox()
    if bb:
        im = im.crop(bb)
    w, h = im.size
    cur = w / max(1, h)
    if abs(cur - target_asp) < 1e-3:
        return im
    if cur > target_asp:
        nh = max(h, int(round(w / target_asp)))
        canvas = Image.new("RGBA", (w, nh), (0, 0, 0, 1))
        canvas.paste(im, (0, (nh - h) // 2), im)
    else:
        nw = max(w, int(round(h * target_asp)))
        canvas = Image.new("RGBA", (nw, h), (0, 0, 0, 1))
        canvas.paste(im, ((nw - w) // 2, 0), im)
    return canvas


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


def letterbox_props_to_footprints(job: Job, *, ids: list[str] | None = None) -> list[str]:
    """Letterbox non-bg sprites to truth footprint aspect (alpha=1 pad)."""
    truth = job.load_truth()
    done = []
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
        out_im = _letterbox_keep_trim(im, box_asp)
        dst = job.new_dir / Path(layer["file"]).name
        out_im.save(dst)
        done.append(lid)
        print(
            f"letterbox {lid} → {dst.name} {out_im.size} "
            f"asp={out_im.size[0]/out_im.size[1]:.3f} box={box_asp:.3f}"
        )
    return done


def post_isolate_normalize(job: Job, *, ids: list[str] | None = None) -> dict:
    """Run after isolate / before compose. Safe to call repeatedly."""
    bg = normalize_bg_to_canvas_aspect(job)
    props = letterbox_props_to_footprints(job, ids=ids)
    return {"bg": str(bg) if bg else None, "letterboxed": props}
