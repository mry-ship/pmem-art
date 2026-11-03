# -*- coding: utf-8 -*-
"""Compose into measured footprints with uniform contain (no squash).

Canvas is tall (W/H≈0.4): a normalized box of width=0.5 height=0.3 is
actually PORTRAIT in pixels. Sprites must match pixel aspect of footprints.
"""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "new_v4"
TRIM = ROOT / "new_v4_trim"
REF = ROOT / "ref_new_full.jpg"
TRUTH = ROOT / "truth_boxes_v4.json"
OUT = ROOT / "_compose_v4_preview.png"
MID = ROOT / "_compose_v4_mid.png"
PLACE = ROOT / "_placements_v4.json"

W, H = 818, 2048
PAD = 500


def trim(im: Image.Image) -> Image.Image:
    bb = im.getchannel("A").getbbox() if im.mode == "RGBA" else None
    return im.crop(bb) if bb else im


def place_scaled(canvas, im, L, T, BW, BH, mode="contain"):
    """Uniform scale; bottom-center. Never squash.
    contain=fit inside box; height=lock box height (width may overflow);
    width=lock box width (height may overflow).
    """
    iw, ih = im.size
    if mode == "height":
        scale = BH / ih
    elif mode == "width":
        scale = BW / iw
    else:
        scale = min(BW / iw, BH / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = L + (BW - nw) // 2
    y = T + BH - nh
    tmp = Image.new("RGBA", (W + PAD * 2, H + PAD * 2), (0, 0, 0, 0))
    tmp.paste(r, (x + PAD, y + PAD), r)
    canvas.alpha_composite(tmp.crop((PAD, PAD, PAD + W, PAD + H)))
    return {"left": x / W, "top": y / H, "width": nw / W, "height": nh / H}


def main():
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    TRIM.mkdir(exist_ok=True)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    placed = []

    for layer in sorted(truth["layers"], key=lambda x: x["z"]):
        name = layer["file"]
        src = SRC / name
        if not src.exists():
            print("MISSING", src)
            continue
        im = Image.open(src)
        if layer["id"] == "bg":
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            canvas.alpha_composite(im.resize((W, H), Image.Resampling.LANCZOS))
            im.resize((W, H), Image.Resampling.LANCZOS).save(TRIM / name)
            info = {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}
        else:
            im = trim(im.convert("RGBA"))
            im.save(TRIM / name)
            L = int(layer["left"] * W)
            T = int(layer["top"] * H)
            BW = int(layer["width"] * W)
            BH = int(layer["height"] * H)
            mode = layer.get("fill", "contain")
            if mode not in ("contain", "height", "width", "cover"):
                mode = "contain"
            px_aspect = BW / BH if BH else 1
            sp_aspect = im.size[0] / im.size[1]
            info = place_scaled(canvas, im, L, T, BW, BH, mode)
            print(
                f"{layer['id']}: {mode} L{info['left']*100:.1f}% T{info['top']*100:.1f}% "
                f"W{info['width']*100:.1f}% H{info['height']*100:.1f}% "
                f"box_px_asp={px_aspect:.2f} spr_asp={sp_aspect:.2f}"
            )

        item = {
            "id": layer["id"],
            "name": layer["name"],
            "note": layer.get("note", ""),
            "z": layer["z"],
            "file": f"new_v4_trim/{name}",
            "truth": {
                "left": layer["left"],
                "top": layer["top"],
                "width": layer["width"],
                "height": layer["height"],
            },
            **info,
        }
        placed.append(item)

    PLACE.write_text(json.dumps(placed, ensure_ascii=False, indent=2), encoding="utf-8")
    ref = Image.open(REF).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    blend = Image.blend(ref, canvas, 0.45)
    board = Image.new("RGB", (W * 3 + 40, H + 20), (30, 36, 44))
    board.paste(ref.convert("RGB"), (10, 10))
    board.paste(canvas.convert("RGB"), (W + 20, 10))
    board.paste(blend.convert("RGB"), (W * 2 + 30, 10))
    board.save(OUT)
    canvas.convert("RGB").save(MID)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
