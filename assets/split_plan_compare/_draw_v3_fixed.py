# -*- coding: utf-8 -*-
import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
plan = json.loads((ROOT / "split_plan_v3_fixed.json").read_text(encoding="utf-8"))
ref = Image.open(ROOT / "ref_full.jpg").convert("RGBA")
W, H = ref.size
guide = ref.copy()
d = ImageDraw.Draw(guide)
hot = {"flower_house", "pond_boat", "flower_lamp"}
for m in plan["modules"]:
    L, T, BW, BH = m["crop"]
    x0, y0 = int(L * W), int(T * H)
    x1, y1 = int((L + BW) * W), int((T + BH) * H)
    col = (255, 80, 80) if m["id"] in hot else (0, 255, 180)
    width = 2 if m["id"] == "bg" else 3
    d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=col + (255,), width=width)
    label = f"{m['name']}\nL,T,W,H={L:.2f},{T:.2f},{BW:.2f},{BH:.2f}"
    d.text((x0 + 3, y0 + 3), label, fill=(255, 255, 0, 255))
out = ROOT / "_crops_guide_v3_fixed.png"
guide.convert("RGB").save(out)
guide.resize((W * 2, H * 2), Image.Resampling.NEAREST).convert("RGB").save(
    ROOT / "_crops_guide_v3_fixed_2x.png"
)
print("wrote", out)
