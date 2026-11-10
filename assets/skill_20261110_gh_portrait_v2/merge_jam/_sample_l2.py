"""Sample L2 cut-face center lightness to detect white pith / hollow."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
out = ROOT / "l2_sample.log"

paths = [
    Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets\cell_l2_fullflesh_r8.jpg"),
    Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets\cell_l2_fullflesh_r8b.jpg"),
    ROOT / "l2_crop_r18.jpg",
    ROOT / "final.jpg",
]

lines: list[str] = []
for p in paths:
    if not p.exists():
        lines.append(f"MISS {p}")
        continue
    im = np.array(Image.open(p).convert("RGB"))
    h, w = im.shape[:2]
    # if full sheet, crop L2
    if w < h * 0.7:  # portrait sheet-ish
        # may be full sheet 9:16
        if h / max(w, 1) > 1.5:
            y0, y1 = 0, h // 4
            x0, x1 = w // 2, w
            cell = im[y0:y1, x0:x1]
        else:
            cell = im
    else:
        cell = im
    ch, cw = cell.shape[:2]
    # sample central band (likely cut faces)
    cy0, cy1 = int(ch * 0.35), int(ch * 0.65)
    cx0, cx1 = int(cw * 0.25), int(cw * 0.75)
    roi = cell[cy0:cy1, cx0:cx1].astype(np.float32)
    # find bright near-white pixels (pith)
    lum = roi.mean(axis=2)
    whiteish = ((roi[:, :, 0] > 200) & (roi[:, :, 1] > 180) & (roi[:, :, 2] > 180)).mean()
    pale_pink = (
        (roi[:, :, 0] > 180)
        & (roi[:, :, 1] > 140)
        & (roi[:, :, 2] > 140)
        & (roi[:, :, 0] - roi[:, :, 1] < 40)
    ).mean()
    magenta = (
        (roi[:, :, 0] > 140)
        & (roi[:, :, 2] > 80)
        & (roi[:, :, 0] > roi[:, :, 1] + 30)
    ).mean()
    dark = (lum < 40).mean()
    # also save a zoom of center
    zoom = Image.fromarray(cell[cy0:cy1, cx0:cx1])
    zpath = ROOT / f"l2_zoom_{p.stem}.jpg"
    zoom.save(zpath, quality=95)
    lines.append(
        f"{p.name}: whiteish={whiteish:.3f} pale_pink={pale_pink:.3f} magenta={magenta:.3f} dark={dark:.3f} meanRGB={roi.mean(axis=(0,1)).round(1).tolist()} -> {zpath.name}"
    )

text = "\n".join(lines) + "\n"
out.write_text(text, encoding="utf-8")
# also print via stderr for pyw
sys.stderr.write(text)
