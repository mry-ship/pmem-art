# -*- coding: utf-8 -*-
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC_DIR = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")
OUT = ROOT / "new_v4"
OUT.mkdir(exist_ok=True)

MAP = {
    "farm77_v4_hay_r2.jpg": "1-干草堆-新.png",
    "farm77_v4_truck.jpg": "2-红卡车-新.png",
    "farm77_v4_shed.jpg": "3-羊棚-新.png",
    "farm77_v4_trough_r2.jpg": "4-食槽-新.png",
    "farm77_v4_farmer.jpg": "5-农夫-新.png",
    "farm77_v4_fence.jpg": "6-栅栏-新.png",
    "farm77_v4_tire_sheep.jpg": "7-轮胎羊-新.png",
    "farm77_v4_path_sheep_r2.jpg": "7b-路上羊-新.png",
    "farm77_v4_water_tire.jpg": "9-轮胎水槽-新.png",
}


def knock_bg(im: Image.Image) -> Image.Image:
    rgba = im.convert("RGBA")
    arr = np.array(rgba)
    rgb = arr[:, :, :3].astype(np.int16)
    white = (rgb[:, :, 0] > 232) & (rgb[:, :, 1] > 232) & (rgb[:, :, 2] > 232)
    light = (rgb.min(axis=2) > 215) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 20)
    c = rgb[3, 3]
    dist = np.abs(rgb - c).sum(axis=2)
    mask = white | light
    if int(c.min()) > 190:
        mask |= dist < 40
    arr[:, :, 3] = np.where(mask, 0, arr[:, :, 3])
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
        cut.save(OUT / dst_name)
        print("wrote", dst_name, cut.size)

    # reuse barn/bg
    for name in ("10-背景-新.png", "8-谷仓-新.png"):
        for folder in ("new_v3", "new_v2"):
            src = ROOT / folder / name
            if src.exists():
                Image.open(src).convert("RGBA").save(OUT / name)
                print("copied", name, "from", folder)
                break


if __name__ == "__main__":
    main()
