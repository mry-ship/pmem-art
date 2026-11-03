# -*- coding: utf-8 -*-
"""Compose new_v2 assets into truth_boxes; write preview + placements + trim."""
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "new_v2"
TRIM = ROOT / "new_v2_trim"
REF = ROOT / "ref_new_full.jpg"
TRUTH = ROOT / "truth_boxes.json"
OUT = ROOT / "_compose_v2_preview.png"
PLACE = ROOT / "_placements_v2.json"

W, H = 818, 2048  # 2x ref
PAD = 500


def trim(im: Image.Image) -> Image.Image:
    bb = im.getchannel("A").getbbox() if im.mode == "RGBA" else None
    return im.crop(bb) if bb else im


def place(
    canvas,
    im,
    L,
    T,
    BW,
    BH,
    anchor: str,
    fill: str = "height",
    clip_box: bool = False,
):
    """Place asset into truth box.
    fill=height: lock visible height to box (width may overflow).
    fill=contain: fit entirely inside box.
    fill=cover: cover entire box (may crop asset).
    clip_box: after placing, crop horizontally into [L, L+BW] so neighbors stay clear.
    """
    iw, ih = im.size
    if fill == "height":
        scale = BH / ih
    elif fill == "width":
        scale = BW / iw
    elif fill == "cover":
        scale = max(BW / iw, BH / ih)
    else:
        scale = min(BW / iw, BH / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)

    if anchor in ("top-left",):
        x, y = L, T
    elif anchor in ("bottom-left",):
        x, y = L, T + BH - nh
    elif anchor in ("bottom-right",):
        x, y = L + BW - nw, T + BH - nh
    elif anchor in ("bottom",):
        x, y = L + (BW - nw) // 2, T + BH - nh
    elif anchor in ("top",):
        x, y = L + (BW - nw) // 2, T
    else:
        x, y = L + (BW - nw) // 2, T + (BH - nh) // 2

    if clip_box:
        # Keep height; carve horizontally into the truth box.
        left_cut = max(0, L - x)
        right_lim = L + BW
        right_cut = max(0, (x + nw) - right_lim)
        if left_cut or right_cut:
            r = r.crop((left_cut, 0, nw - right_cut, nh))
            nw = r.size[0]
            x = max(x, L)

    tmp = Image.new("RGBA", (W + PAD * 2, H + PAD * 2), (0, 0, 0, 0))
    tmp.paste(r, (x + PAD, y + PAD), r)
    canvas.alpha_composite(tmp.crop((PAD, PAD, PAD + W, PAD + H)))
    return {
        "left": x / W,
        "top": y / H,
        "width": nw / W,
        "height": nh / H,
    }


def main():
    truth = json.loads(TRUTH.read_text(encoding="utf-8"))
    TRIM.mkdir(exist_ok=True)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    placed = []

    for layer in sorted(truth["layers"], key=lambda x: x["z"]):
        name = layer["file"]
        src = SRC / name
        if not src.exists():
            raise FileNotFoundError(src)
        im = Image.open(src)
        if layer["id"] == "bg":
            if im.mode != "RGBA":
                im = im.convert("RGBA")
            canvas.alpha_composite(im.resize((W, H), Image.Resampling.LANCZOS))
            info = {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}
            # still save a copy
            im.resize((W, H), Image.Resampling.LANCZOS).save(TRIM / name)
        else:
            im = im.convert("RGBA")
            # Spatial-lock layers (full-canvas sheep etc.) must NOT be alpha-trimmed
            # or the empty padding that encodes original positions is destroyed.
            spatial_lock = (
                layer.get("fill") == "cover"
                and layer.get("width", 0) >= 0.99
                and layer.get("height", 0) >= 0.99
            )
            if not spatial_lock:
                im = trim(im)
            im.save(TRIM / name)
            L = int(layer["left"] * W)
            T = int(layer["top"] * H)
            BW = int(layer["width"] * W)
            BH = int(layer["height"] * H)
            fill = layer.get("fill") or (
                "width" if layer["id"] == "fence" else "height"
            )
            if spatial_lock:
                # Exact canvas cover — already authored at locked coords.
                r = im.resize((W, H), Image.Resampling.LANCZOS)
                canvas.alpha_composite(r)
                info = {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}
            else:
                info = place(
                    canvas, im, L, T, BW, BH,
                    layer.get("anchor", "bottom"),
                    fill=fill,
                    clip_box=bool(layer.get("clip_box")),
                )

        item = {
            "id": layer["id"],
            "name": layer["name"],
            "note": layer.get("note", ""),
            "z": layer["z"],
            "file": f"new_v2_trim/{name}",
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
            f"{layer['id']}: placed L{info['left']*100:.1f}% T{info['top']*100:.1f}% "
            f"W{info['width']*100:.1f}% H{info['height']*100:.1f}% "
            f"(truth H{layer['height']*100:.0f}%)"
        )

    PLACE.write_text(json.dumps(placed, ensure_ascii=False, indent=2), encoding="utf-8")

    ref = Image.open(REF).convert("RGBA").resize((W, H), Image.Resampling.LANCZOS)
    blend = Image.blend(ref, canvas, 0.45)
    # also draw truth boxes on blend corner strip? skip
    board = Image.new("RGB", (W * 3 + 40, H + 20), (30, 36, 44))
    board.paste(ref.convert("RGB"), (10, 10))
    board.paste(canvas.convert("RGB"), (W + 20, 10))
    board.paste(blend.convert("RGB"), (W * 2 + 30, 10))
    board.save(OUT)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
