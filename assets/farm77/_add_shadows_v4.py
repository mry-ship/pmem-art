# -*- coding: utf-8 -*-
"""Add soft contact shadows under isolated sprites that lost grounding."""
from pathlib import Path
from PIL import Image, ImageFilter, ImageDraw

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "new_v4"

NEED = [
    "2-红卡车-新.png",
    "8-谷仓-新.png",
    "9-轮胎水槽-新.png",
]


def add_contact_shadow(im: Image.Image, blur=28, alpha=120, y_offset=6, v_scale=0.22) -> Image.Image:
    im = im.convert("RGBA")
    a = im.getchannel("A")
    bb = a.getbbox()
    if not bb:
        return im
    l, t, r, b = bb
    w, h = r - l, b - t
    sw, sh = max(8, int(w * 0.85)), max(6, int(h * v_scale))
    cx = (l + r) // 2
    cy = b - sh // 3 + y_offset
    mask = Image.new("L", (sw, sh), 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((0, 0, sw - 1, sh - 1), fill=alpha)
    mask = mask.filter(ImageFilter.GaussianBlur(blur))
    black = Image.new("RGBA", (sw, sh), (20, 12, 8, 255))
    black.putalpha(mask)
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    layer.alpha_composite(black, (cx - sw // 2, cy - sh // 2))
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(layer)
    out.alpha_composite(im)
    return out


def main():
    for name in NEED:
        p = SRC / name
        if not p.exists():
            print("MISSING", p)
            continue
        out = add_contact_shadow(Image.open(p))
        out.save(p)
        print("shadowed", name, out.size)


if __name__ == "__main__":
    main()
