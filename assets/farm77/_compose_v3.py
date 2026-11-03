# -*- coding: utf-8 -*-
"""Compose new_v3 cutouts into their crop boxes. Overlap/occlusion allowed."""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "new_v3"
TRIM = ROOT / "new_v3_trim"
REF = ROOT / "ref_new_full.jpg"
TRUTH = ROOT / "truth_boxes_v3.json"
OUT = ROOT / "_compose_v3_preview.png"
PLACE = ROOT / "_placements_v3.json"

W, H = 818, 2048
PAD = 500


def trim(im: Image.Image) -> Image.Image:
    bb = im.getchannel("A").getbbox() if im.mode == "RGBA" else None
    return im.crop(bb) if bb else im


def place_in_box(canvas, im, L, T, BW, BH, fill="cover"):
    """Uniform scale into crop box.
    cover (default): fill the original crop footprint exactly (may crop asset edges).
    This locks on-screen size to the cut taken from the reference.
    Overlaps between modules are intentional (occlusion).
    """
    iw, ih = im.size
    if fill == "width":
        scale = BW / iw
    elif fill == "contain":
        scale = min(BW / iw, BH / ih)
    elif fill == "height":
        scale = BH / ih
    else:
        scale = max(BW / iw, BH / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)
    x = L + (BW - nw) // 2
    y = T + (BH - nh) // 2
    # Clip to the crop box so footprint matches original cut.
    if fill in ("cover", "height", "contain"):
        left_cut = max(0, L - x)
        top_cut = max(0, T - y)
        right_lim = L + BW
        bot_lim = T + BH
        right_cut = max(0, (x + nw) - right_lim)
        bot_cut = max(0, (y + nh) - bot_lim)
        if left_cut or top_cut or right_cut or bot_cut:
            r = r.crop((left_cut, top_cut, nw - right_cut, nh - bot_cut))
            nw, nh = r.size
            x, y = max(x, L), max(y, T)
    tmp = Image.new("RGBA", (W + PAD * 2, H + PAD * 2), (0, 0, 0, 0))
    tmp.paste(r, (x + PAD, y + PAD), r)
    canvas.alpha_composite(tmp.crop((PAD, PAD, PAD + W, PAD + H)))
    return {"left": x / W, "top": y / H, "width": nw / W, "height": nh / H}


def main():
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    TRIM.mkdir(exist_ok=True)
    SRC.mkdir(exist_ok=True)
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
            fill = "width" if layer["id"] == "fence" else "cover"
            info = place_in_box(canvas, im, L, T, BW, BH, fill=fill)

        item = {
            "id": layer["id"],
            "name": layer["name"],
            "note": layer.get("note", ""),
            "z": layer["z"],
            "file": f"new_v3_trim/{name}",
            "truth": {
                "left": layer["left"],
                "top": layer["top"],
                "width": layer["width"],
                "height": layer["height"],
            },
            **info,
        }
        placed.append(item)
        print(
            f"{layer['id']}: L{info['left']*100:.1f}% T{info['top']*100:.1f}% "
            f"W{info['width']*100:.1f}% H{info['height']*100:.1f}% "
            f"(box H{layer['height']*100:.0f}%)"
        )

    PLACE.write_text(json.dumps(placed, ensure_ascii=False, indent=2), encoding="utf-8")
    ref = Image.open(REF).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    blend = Image.blend(ref, canvas, 0.45)
    board = Image.new("RGB", (W * 3 + 40, H + 20), (30, 36, 44))
    board.paste(ref.convert("RGB"), (10, 10))
    board.paste(canvas.convert("RGB"), (W + 20, 10))
    board.paste(blend.convert("RGB"), (W * 2 + 30, 10))
    board.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
