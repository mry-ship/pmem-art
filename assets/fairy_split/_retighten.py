# -*- coding: utf-8 -*-
from pathlib import Path
import json
from PIL import Image

root = Path(__file__).resolve().parent
print("=== sprite aspects ===")
for f in sorted((root / "new").glob("*.png")):
    im = Image.open(f).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if not bb:
        print(f.name, "empty")
        continue
    t = im.crop(bb)
    print(f.name, "asp", round(t.size[0] / t.size[1], 3), t.size)

t = json.loads((root / "truth_boxes.json").read_text(encoding="utf-8"))
upd = {
    "flower_house": dict(left=0.08, top=0.18, width=0.52, height=0.40),
    "treehouse": dict(left=0.48, top=0.12, width=0.50, height=0.42),
    "mushrooms": dict(left=0.0, top=0.42, width=0.26, height=0.18),
    "pond_boat": dict(left=0.02, top=0.52, width=0.42, height=0.18),
    "food_mushroom": dict(left=0.55, top=0.60, width=0.44, height=0.24),
    "mole": dict(left=0.60, top=0.50, width=0.38, height=0.20),
    "flying_fairy": dict(left=0.35, top=0.42, width=0.32, height=0.18),
    "violinist": dict(left=0.22, top=0.56, width=0.42, height=0.34),
    "flower_lamp": dict(left=0.0, top=0.64, width=0.30, height=0.30),
}
for L in t["layers"]:
    if L["id"] in upd:
        L.update(upd[L["id"]])
        L["fill"] = "contain"
(root / "truth_boxes.json").write_text(
    json.dumps(t, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("boxes tightened")
