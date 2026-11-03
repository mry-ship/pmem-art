# -*- coding: utf-8 -*-
"""Export crops + guide + truth_boxes from split_plan; print pixel aspects."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
PLAN = json.loads((ROOT / "split_plan.json").read_text(encoding="utf-8"))
REF = Image.open(ROOT / PLAN["ref"]).convert("RGBA")
W, H = REF.size
OUT = ROOT / "_crops"
OUT.mkdir(exist_ok=True)


def size_for(pa: float) -> str:
    if pa < 0.85:
        return "1024x1536"
    if pa > 1.2:
        return "1536x1024"
    return "1024x1024"


def main():
    guide = REF.copy()
    d = ImageDraw.Draw(guide)
    layers = []
    for m in PLAN["modules"]:
        L, T, BW, BH = m["crop"]
        x0, y0 = int(L * W), int(T * H)
        x1, y1 = int((L + BW) * W), int((T + BH) * H)
        crop = REF.crop((x0, y0, x1, y1))
        crop.save(OUT / f"{m['id']}.png")
        pa = (BW / BH) * (W / H) if BH else 1.0
        sz = m.get("size") or size_for(pa)
        m["_pixel_aspect"] = round(pa, 3)
        m["_size"] = sz
        print(f"{m['id']}: crop {crop.size} px_asp={pa:.3f} size={sz}")
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(0, 255, 180), width=2)
        d.text((x0 + 3, y0 + 3), m["id"], fill=(255, 255, 0))
        layers.append(
            {
                "id": m["id"],
                "name": m["name"],
                "z": m["z"],
                "file": m["file"],
                "left": L,
                "top": T,
                "width": BW,
                "height": BH,
                "anchor": "bottom-left",
                "fill": "cover" if m["id"] == "bg" else "contain",
                "note": m.get("keep", "")[:80],
                "size": sz,
                "keep": m.get("keep", ""),
                "remove": m.get("remove", ""),
            }
        )
    truth = {
        "ref": PLAN["ref"],
        "canvas": {"w": W, "h": H, "aspect": W / H},
        "method": "pmem-layer-split",
        "layers": layers,
    }
    (ROOT / "truth_boxes.json").write_text(
        json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (ROOT / "split_plan.json").write_text(
        json.dumps(PLAN, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    guide.convert("RGB").save(ROOT / "_crops_guide.png")
    print("wrote truth_boxes.json + _crops_guide.png")


if __name__ == "__main__":
    main()
