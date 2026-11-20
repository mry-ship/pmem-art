# -*- coding: utf-8 -*-
"""Frozen footprints = position + size contract for restore-quality compose."""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from .job import Job, save_json


def resolve_bg_plate(job: Job) -> Path | None:
    for p in (
        job.new_dir / "10-bg.png",
        job.trim_dir / "10-bg.png",
        job.new_dir / "bg.png",
        job.root / "new" / "10-bg.png",
    ):
        if p.exists():
            return p
    return None


def diff_subject_mask(
    ref_rgb: np.ndarray,
    bg_rgb: np.ndarray,
    *,
    thr: float = 22.0,
) -> np.ndarray:
    """Boolean mask where ref differs from empty-stage bg (subject/prop pixels)."""
    if ref_rgb.shape != bg_rgb.shape:
        _lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
        bg_im = Image.fromarray(bg_rgb).resize(
            (ref_rgb.shape[1], ref_rgb.shape[0]), _lanczos
        )
        bg_rgb = np.asarray(bg_im.convert("RGB"))
    diff = np.abs(ref_rgb.astype(np.float32) - bg_rgb.astype(np.float32)).mean(axis=2)
    return diff >= thr


def expand_norm_box(
    left: float,
    top: float,
    width: float,
    height: float,
    *,
    pad: float = 0.04,
) -> tuple[float, float, float, float]:
    """Grow a norm box by `pad` on each side, clamped to [0,1]."""
    L = max(0.0, float(left) - pad)
    T = max(0.0, float(top) - pad)
    R = min(1.0, float(left) + float(width) + pad)
    B = min(1.0, float(top) + float(height) + pad)
    return L, T, max(0.01, R - L), max(0.01, B - T)


def tighten_norm_box_with_mask(
    mask: np.ndarray,
    left: float,
    top: float,
    width: float,
    height: float,
    *,
    pad: float = 0.05,
    min_keep: float = 0.35,
) -> tuple[float, float, float, float]:
    """Shrink a norm box to the subject mask inside it (+ generous pad).

    If mask coverage is too weak, return the original box unchanged.
    """
    H, W = mask.shape[:2]
    x0 = int(max(0, left * W))
    y0 = int(max(0, top * H))
    x1 = int(min(W, (left + width) * W))
    y1 = int(min(H, (top + height) * H))
    if x1 <= x0 + 2 or y1 <= y0 + 2:
        return left, top, width, height
    region = mask[y0:y1, x0:x1]
    if region.size == 0 or float(region.mean()) < 0.02:
        return left, top, width, height
    ys, xs = np.where(region)
    if len(xs) < 12:
        return left, top, width, height
    # content bbox in full-image pixels
    cx0 = x0 + int(xs.min())
    cy0 = y0 + int(ys.min())
    cx1 = x0 + int(xs.max()) + 1
    cy1 = y0 + int(ys.max()) + 1
    # pad in norm space
    pw, ph = pad * W, pad * H
    cx0 = max(0, int(cx0 - pw))
    cy0 = max(0, int(cy0 - ph))
    cx1 = min(W, int(cx1 + pw))
    cy1 = min(H, int(cy1 + ph))
    nL, nT = cx0 / W, cy0 / H
    nW, nH = (cx1 - cx0) / W, (cy1 - cy0) / H
    # don't shrink more than (1-min_keep) of original area span
    if nW < width * min_keep or nH < height * min_keep:
        return left, top, width, height
    # never expand beyond original box
    nL = max(left, nL)
    nT = max(top, nT)
    nR = min(left + width, nL + nW)
    nB = min(top + height, nT + nH)
    return float(nL), float(nT), float(max(0.01, nR - nL)), float(max(0.01, nB - nT))


def crop_content_norm_box(
    crop_rgb: np.ndarray,
    *,
    thr: float = 16.0,
    pad_px: int = 2,
) -> tuple[float, float, float, float] | None:
    """Norm box of non-border-like content inside a crop tile (0..1 within crop).

    Uses distance from median border color — good fallback when empty-bg plate
    is unreliable (mask_frac too high).
    """
    h, w = crop_rgb.shape[:2]
    if h < 8 or w < 8:
        return None
    border = np.concatenate(
        [
            crop_rgb[0, :, :],
            crop_rgb[-1, :, :],
            crop_rgb[:, 0, :],
            crop_rgb[:, -1, :],
        ],
        axis=0,
    )
    med = np.median(border.astype(np.float32), axis=0)
    dist = np.linalg.norm(crop_rgb.astype(np.float32) - med, axis=2)
    mask = dist >= thr
    if float(mask.mean()) < 0.04 or float(mask.mean()) > 0.92:
        return None
    ys, xs = np.where(mask)
    if len(xs) < 12:
        return None
    x0 = max(0, int(xs.min()) - pad_px)
    y0 = max(0, int(ys.min()) - pad_px)
    x1 = min(w, int(xs.max()) + 1 + pad_px)
    y1 = min(h, int(ys.max()) + 1 + pad_px)
    return x0 / w, y0 / h, (x1 - x0) / w, (y1 - y0) / h


def map_crop_content_to_full(
    left: float,
    top: float,
    width: float,
    height: float,
    content: tuple[float, float, float, float],
) -> tuple[float, float, float, float]:
    """Map content norm-in-crop → full-image norm box."""
    cl, ct, cw, ch = content
    return (
        left + cl * width,
        top + ct * height,
        max(0.01, cw * width),
        max(0.01, ch * height),
    )


def write_footprints(job: Job, truth: dict) -> Path:
    """Freeze placement contract: position + size in norm and pixels."""
    cw = int(truth["canvas"]["w"])
    ch = int(truth["canvas"]["h"])
    layers = []
    for L in truth.get("layers") or []:
        left = float(L["left"])
        top = float(L["top"])
        width = float(L["width"])
        height = float(L["height"])
        x0, y0 = int(left * cw), int(top * ch)
        x1, y1 = int((left + width) * cw), int((top + height) * ch)
        layers.append(
            {
                "id": L["id"],
                "left": left,
                "top": top,
                "width": width,
                "height": height,
                "px": [x0, y0, x1, y1],
                "anchor": L.get("anchor", "bottom-center"),
                "grounded": L.get("grounded"),
                "locked": True,
            }
        )
    data = {
        "ref": truth.get("ref"),
        "canvas": {"w": cw, "h": ch},
        "note": "FROZEN position+size contract. compose/gate must use these boxes; "
        "do NOT widen to pass fill/asp. Re-isolate sprites instead.",
        "layers": layers,
    }
    out = job.root / "_footprints.json"
    save_json(out, data)
    return out
