# -*- coding: utf-8 -*-
"""Ingest Cursor GenerateImage JPGs → RGBA cutouts in new_v3/."""
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC_DIR = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")
OUT = ROOT / "new_v3"
OUT.mkdir(exist_ok=True)

MAP = {
    "farm77_v3_hay.jpg": "1-干草堆-新.png",
    "farm77_v3_truck_r2.jpg": "2-红卡车-新.png",
    "farm77_v3_shed_r2.jpg": "3-羊棚-新.png",
    "farm77_v3_trough.jpg": "4-食槽-新.png",
    "farm77_v3_farmer.jpg": "5-农夫-新.png",
    "farm77_v3_tire_sheep.jpg": "7-轮胎羊-新.png",
    "farm77_v3_path_sheep.jpg": "7b-路上羊-新.png",
    "farm77_v3_fence.jpg": "6-栅栏-新.png",
    "farm77_v3_water_tire.jpg": "9-轮胎水槽-新.png",
}


def knock_bg(im: Image.Image) -> Image.Image:
    """Remove near-white / light-gray studio backgrounds to alpha."""
    rgba = im.convert("RGBA")
    arr = np.array(rgba)
    rgb = arr[:, :, :3].astype(np.int16)
    # near-white background
    white = (rgb[:, :, 0] > 235) & (rgb[:, :, 1] > 235) & (rgb[:, :, 2] > 235)
    # very light gray
    light = (rgb.min(axis=2) > 220) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 18)
    # checker soft detect: high local variance of near-white — skip, use corner flood
    mask = white | light
    # also clear pixels very similar to top-left corner color
    c = rgb[2, 2]
    dist = np.abs(rgb.astype(np.int16) - c).sum(axis=2)
    if c.min() > 200:
        mask |= dist < 35
    alpha = arr[:, :, 3]
    alpha[mask] = 0
    arr[:, :, 3] = alpha
    out = Image.fromarray(arr, "RGBA")
    bb = out.getchannel("A").getbbox()
    return out.crop(bb) if bb else out


def main():
    for src_name, dst_name in MAP.items():
        src = SRC_DIR / src_name
        if not src.exists():
            print("missing", src)
            continue
        cut = knock_bg(Image.open(src))
        dst = OUT / dst_name
        cut.save(dst)
        print("wrote", dst.name, cut.size)


if __name__ == "__main__":
    main()
