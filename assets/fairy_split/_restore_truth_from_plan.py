# -*- coding: utf-8 -*-
"""Restore truth_boxes from split_plan crops (calibrated footprints)."""
import json
from pathlib import Path

root = Path(__file__).resolve().parent
plan = json.loads((root / "split_plan.json").read_text(encoding="utf-8"))
ref = root / plan["ref"]
from PIL import Image

W, H = Image.open(ref).size
layers = []
for m in plan["modules"]:
    l, t, w, h = m["crop"]
    entry = {
        "id": m["id"],
        "name": m["name"],
        "z": m["z"],
        "file": m["file"],
        "left": round(l, 4),
        "top": round(t, 4),
        "width": round(w, 4),
        "height": round(h, 4),
    }
    if "grounded" in m:
        entry["grounded"] = m["grounded"]
    if "fill" in m:
        entry["fill"] = m["fill"]
    if "mode" in m:
        entry["mode"] = m["mode"]
    layers.append(entry)

truth = {"canvas": {"w": W, "h": H}, "layers": layers}
(root / "truth_boxes.json").write_text(
    json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(f"restored {len(layers)} layers @ {W}x{H}")
for L in layers:
    if L["id"] == "bg":
        continue
    px = L["width"] / L["height"] * (W / H)
    print(f"  {L['id']}: L{L['left']:.3f} T{L['top']:.3f} W{L['width']:.3f} H{L['height']:.3f} px={px:.3f}")
