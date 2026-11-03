# -*- coding: utf-8 -*-
from pathlib import Path
import json
from PIL import Image

ROOT = Path(__file__).resolve().parent
TRIM = ROOT / "new_trim"
NEW = ROOT / "new"
REF = ROOT / "ref_new_full.jpg"
OUT = ROOT / "_compose_preview.png"
CSS_OUT = ROOT / "_placements.json"
W, H = 818, 2048


def ensure_trim(name: str) -> Image.Image:
    src = NEW / name
    # allow using flip truck if requested via name
    dst = TRIM / name
    TRIM.mkdir(exist_ok=True)
    im = Image.open(src).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if bb:
        im = im.crop(bb)
    im.save(dst)
    return im


def place(canvas, im, L, T, BW, BH, mode="height-bottom"):
    iw, ih = im.size
    if "height" in mode:
        scale = BH / ih
    elif "width" in mode:
        scale = BW / iw
    elif "cover" in mode:
        scale = max(BW / iw, BH / ih)
    else:
        scale = min(BW / iw, BH / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    r = im.resize((nw, nh), Image.Resampling.LANCZOS)

    x = L + (BW - nw) // 2
    y = T + (BH - nh) // 2
    if "top-left" in mode:
        x, y = L, T
    elif "bottom-right" in mode:
        # for width mode, BH may not match nh — sit on box bottom, flush right
        x, y = L + BW - nw, T + BH - nh
    elif "bottom-left" in mode:
        x, y = L, T + BH - nh
    elif "bottom" in mode:
        x, y = L + (BW - nw) // 2, T + BH - nh
    elif "left" in mode:
        x, y = L, T + (BH - nh) // 2

    pad = 500
    tmp = Image.new("RGBA", (W + pad * 2, H + pad * 2), (0, 0, 0, 0))
    tmp.paste(r, (x + pad, y + pad), r)
    canvas.alpha_composite(tmp.crop((pad, pad, pad + W, pad + H)))
    return {"left": x / W, "top": y / H, "width": nw / W, "height": nh / H}


def main():
    # Visible-frame match: force height like original; allow side overflow crop.
    placements = [
        ("bg", "10-背景-新.png", 0, 0, 1, 1, "full"),
        # barn ~30% H, overflow left/top OK
        ("barn", "8-谷仓-新.png", -0.15, 0.02, 0.88, 0.30, "height-top-left"),
        # truck faces BOTTOM-LEFT; mid-upper; ~22% H
        ("truck", "2-红卡车-新.png", -0.02, 0.17, 0.72, 0.24, "height-bottom"),
        # shed: width ~55% on right (height follows asset)
        ("shed", "3-羊棚-新.png", 0.48, 0.26, 0.58, 0.30, "width-bottom-right"),
        ("hay", "1-干草堆-新.png", -0.04, 0.35, 0.46, 0.18, "height-bottom-left"),
        ("tire", "9-轮胎水槽-新.png", 0.48, 0.47, 0.32, 0.11, "height-bottom"),
        ("trough", "4-食槽-新.png", 0.48, 0.43, 0.50, 0.15, "height-bottom"),
        ("farmer", "5-农夫-新.png", 0.16, 0.30, 0.42, 0.32, "height-bottom"),
        ("sheep", "7-羊群-新.png", -0.02, 0.50, 0.95, 0.22, "height-bottom-left"),
        ("fence", "6-栅栏-新.png", -0.06, 0.60, 1.12, 0.20, "width-bottom"),
    ]

    labels = {
        "bg": "10 背景", "barn": "8 谷仓", "truck": "2 红卡车", "shed": "3 羊棚",
        "hay": "1 干草堆", "tire": "9 轮胎水槽", "trough": "4 食槽",
        "farmer": "5 农夫", "sheep": "7 羊群", "fence": "6 栅栏",
    }
    notes = {
        "bg": "天空远树雪地",
        "barn": "大谷仓，可溢出裁切",
        "truck": "朝左下（已纠正）",
        "shed": "右侧羊棚",
        "hay": "左侧草垛",
        "tire": "结冰轮胎",
        "trough": "食槽",
        "farmer": "农夫抱小羊",
        "sheep": "自由羊",
        "fence": "前景栅栏最前",
    }

    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    css = []
    for key, name, l, t, w, h, mode in placements:
        im = ensure_trim(name)
        if mode == "full":
            canvas.alpha_composite(im.resize((W, H), Image.Resampling.LANCZOS))
            info = {"left": 0.0, "top": 0.0, "width": 1.0, "height": 1.0}
        else:
            info = place(
                canvas, im,
                int(l * W), int(t * H), int(w * W), int(h * H),
                mode=mode,
            )
        item = {
            "id": key, "file": f"new_trim/{name}", "src_file": name,
            "name": labels[key], "note": notes[key], "z": len(css) + 1, **info,
        }
        css.append(item)
        print(
            f"{key}: L{info['left']*100:.1f}% T{info['top']*100:.1f}% "
            f"W{info['width']*100:.1f}% H{info['height']*100:.1f}%"
        )

    CSS_OUT.write_text(json.dumps(css, ensure_ascii=False, indent=2), encoding="utf-8")
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
