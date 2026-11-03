# -*- coding: utf-8 -*-
"""Export padded crops from ref per split_plan_v3.json."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "split_plan_v3.json").read_text(encoding="utf-8"))
REF = Image.open(ROOT / PLAN["ref"]).convert("RGBA")
W, H = REF.size
OUT = ROOT / "_crops_v3"
OUT.mkdir(exist_ok=True)


def clamp_box(l, t, w, h, pad=0.0):
    l = max(0.0, l - pad)
    t = max(0.0, t - pad)
    r = min(1.0, l + w + 2 * pad)
    b = min(1.0, t + h + 2 * pad)
    return l, t, r - l, b - t


def main():
    guide = REF.copy()
    d = ImageDraw.Draw(guide)
    boxes = {}
    for m in PLAN["modules"]:
        if m.get("mode") == "full" or m.get("prompt") == "skip":
            continue
        l, t, w, h = m["crop"]
        pad = float(m.get("pad", 0.0))
        L, T, BW, BH = clamp_box(l, t, w, h, pad)
        box = {
            "left": L,
            "top": T,
            "width": BW,
            "height": BH,
            "src_crop": m["crop"],
        }
        boxes[m["id"]] = box
        x0, y0 = int(L * W), int(T * H)
        x1, y1 = int((L + BW) * W), int((T + BH) * H)
        crop = REF.crop((x0, y0, x1, y1))
        path = OUT / f"{m['id']}.png"
        crop.save(path)
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(0, 255, 180), width=2)
        d.text((x0 + 4, y0 + 4), m["id"], fill=(255, 255, 0))
        print(f"{m['id']}: {crop.size} -> {path.name} box=({L:.3f},{T:.3f},{BW:.3f},{BH:.3f})")

    (ROOT / "truth_boxes_v3.json").write_text(
        json.dumps(
            {
                "ref": PLAN["ref"],
                "canvas": {"w": W, "h": H, "aspect": W / H},
                "method": "crop_then_prompt",
                "notes": PLAN["notes"],
                "layers": [
                    {
                        "id": m["id"],
                        "name": m["name"],
                        "z": m["z"],
                        "file": m["file"],
                        "left": boxes.get(m["id"], {"left": 0})["left"] if m["id"] != "bg" else 0.0,
                        "top": boxes.get(m["id"], {"top": 0})["top"] if m["id"] != "bg" else 0.0,
                        "width": boxes.get(m["id"], {"width": 1})["width"] if m["id"] != "bg" else 1.0,
                        "height": boxes.get(m["id"], {"height": 1})["height"] if m["id"] != "bg" else 1.0,
                        "anchor": "top-left",
                        "fill": "contain",
                        "note": m.get("keep", ""),
                    }
                    for m in PLAN["modules"]
                    if m["id"] == "bg" or m["id"] in boxes
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    guide.save(ROOT / "_crops_v3_guide.png")
    print("wrote truth_boxes_v3.json + _crops_v3_guide.png")


if __name__ == "__main__":
    main()
