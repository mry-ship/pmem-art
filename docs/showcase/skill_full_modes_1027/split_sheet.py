"""Merge contact sheet → 8 equal square tiles.

Reliable path for soft-shadow / faint-grid sheets:
1) densest horizontal band (skip empty grid rows)
2) equal 8 columns
3) each column → centered on one shared square canvas (sheet BG)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image


def bg_rgb(arr: np.ndarray) -> np.ndarray:
    ring = np.concatenate(
        [arr[:8, :].reshape(-1, 3), arr[-8:, :].reshape(-1, 3), arr[:, :8].reshape(-1, 3), arr[:, -8:].reshape(-1, 3)],
        axis=0,
    )
    return np.median(ring, axis=0)


def densest_band(mask: np.ndarray) -> tuple[int, int]:
    """Prefer object rows (localized mass) over full-width grid lines."""
    H, W = mask.shape
    row_sum = mask.sum(axis=1).astype(np.float32)
    row_std = mask.astype(np.float32).std(axis=1)
    # grid lines: high sum, low std; objects: mid sum, high std
    score = row_sum * (row_std + 0.05)
    if score.max() <= 0:
        return int(H * 0.25), int(H * 0.75)
    peak = int(np.argmax(score))
    thr = max(score.max() * 0.22, 1.0)
    lo = peak
    while lo > 0 and score[lo - 1] >= thr * 0.4:
        lo -= 1
    hi = peak
    while hi < H - 1 and score[hi + 1] >= thr * 0.4:
        hi += 1
    span = max(hi - lo + 1, int(H * 0.2))
    win = int(np.clip(span * 1.15, H * 0.24, H * 0.42))
    y0 = int(np.clip(peak - win // 2, 0, H - win))
    return y0, y0 + win


def split_to_squares(src: Path, outdir: Path, n: int = 8) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im)
    H, W, _ = arr.shape
    bg = bg_rgb(arr)
    dist = np.linalg.norm(arr.astype(np.float32) - bg.astype(np.float32), axis=2)
    mask = dist > 18.0
    # kill 1px grids
    a = mask.astype(np.uint8)
    neigh = (
        np.pad(a, 1)[:-2, 1:-1]
        + np.pad(a, 1)[2:, 1:-1]
        + np.pad(a, 1)[1:-1, :-2]
        + np.pad(a, 1)[1:-1, 2:]
    )
    mask = (a == 1) & (neigh >= 2)

    y0, y1 = densest_band(mask)
    band_im = im.crop((0, y0, W, y1))
    bh = y1 - y0
    # shared square: max(band height, column width) with small margin
    col_w = W / n
    side = int(max(bh, col_w) * 1.06)
    side = max(280, side)
    if side % 2:
        side += 1
    bg_t = tuple(int(round(c)) for c in bg)

    for i in range(n):
        x0 = int(round(i * W / n))
        x1 = int(round((i + 1) * W / n))
        cell = band_im.crop((x0, 0, x1, bh))
        canvas = Image.new("RGB", (side, side), bg_t)
        cw, ch = cell.size
        # fit whole cell into square (letterbox on BG) — keeps full object in-column
        fit = side * 0.92
        sc = min(fit / cw, fit / ch)
        nw, nh = max(1, int(cw * sc)), max(1, int(ch * sc))
        canvas.paste(cell.resize((nw, nh), Image.Resampling.LANCZOS), ((side - nw) // 2, (side - nh) // 2))
        canvas.save(outdir / f"L{i + 1:02d}.jpg", quality=93)

    print(f"split {src.name} -> {outdir} band=y[{y0}:{y1}] side={side} equal-{n}")


if __name__ == "__main__":
    split_to_squares(Path(sys.argv[1]), Path(sys.argv[2]))
