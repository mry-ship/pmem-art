# -*- coding: utf-8 -*-
from PIL import Image
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
PARTS = ROOT / "new_v2" / "_sheep_parts"
W, H = 818, 2048


def trim(im):
    bb = im.getchannel("A").getbbox()
    return im.crop(bb) if bb else im


def paste_box(canvas, path, box):
    L, T, BW, BH = [int(v * s) for v, s in zip(box, (W, H, W, H))]
    im = trim(Image.open(path).convert("RGBA"))
    iw, ih = im.size
    scale = min(BH / ih, BW / iw)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = L + max(0, (BW - nw) // 2)
    y = T + BH - nh
    tmp = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    tmp.paste(r, (x, y), r)
    canvas.alpha_composite(tmp)
    print(path.name, f"L{x/W:.3f} T{y/H:.3f} W{nw/W:.3f} H{nh/H:.3f}")


def main():
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    paste_box(canvas, PARTS / "tire.png", (0.02, 0.50, 0.28, 0.17))
    paste_box(canvas, PARTS / "trough.png", (0.56, 0.40, 0.36, 0.13))
    paste_box(canvas, PARTS / "path.png", (0.55, 0.57, 0.28, 0.12))
    out = ROOT / "new_v2" / "7-羊群-新.png"
    canvas.save(out)
    print("wrote", out)

    truth_path = ROOT / "truth_boxes.json"
    t = json.loads(truth_path.read_text(encoding="utf-8"))
    for layer in t["layers"]:
        if layer["id"] == "hay":
            layer["height"] = 0.17
            layer["top"] = 0.34
            layer["width"] = 0.34
        if layer["id"] == "fence":
            layer["fill"] = "width"
            layer["top"] = 0.62
            layer["height"] = 0.20
            layer["left"] = 0.0
            layer["width"] = 1.0
            layer["anchor"] = "bottom-left"
    truth_path.write_text(json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8")
    print("truth updated")


if __name__ == "__main__":
    main()
