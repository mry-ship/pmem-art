# -*- coding: utf-8 -*-
"""Tighten truth boxes to match isolated sprite aspect; keep bottom + center-x."""
import json
from pathlib import Path
from PIL import Image

root = Path(__file__).resolve().parent
truth = json.loads((root / "truth_boxes.json").read_text(encoding="utf-8"))
W, H = truth["canvas"]["w"], truth["canvas"]["h"]
new = root / "new"

for L in truth["layers"]:
    if L["id"] == "bg":
        continue
    src = new / Path(L["file"]).name
    if not src.exists():
        continue
    im = Image.open(src).convert("RGBA")
    bb = im.getchannel("A").getbbox()
    if not bb:
        continue
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    spr = tw / th
    cx = L["left"] + L["width"] / 2
    bottom = L["top"] + L["height"]
    nh = L["height"]
    # box_px_asp = (nw/nh)*(W/H) == spr  =>  nw = spr * nh * (H/W)
    nw = spr * nh * (H / W)
    if nw > 0.98:
        nw = min(0.98, max(L["width"], 0.2))
        nh = nw * (W / H) / spr
    L["width"] = round(max(0.05, min(1.0, nw)), 4)
    L["height"] = round(max(0.05, min(1.0, nh)), 4)
    L["left"] = round(max(0.0, min(1.0 - L["width"], cx - L["width"] / 2)), 4)
    L["top"] = round(max(0.0, min(1.0 - L["height"], bottom - L["height"])), 4)
    px = L["width"] / L["height"] * (W / H)
    print(
        f"{L['id']}: spr={spr:.2f} -> "
        f"L{L['left']:.3f} T{L['top']:.3f} W{L['width']:.3f} H{L['height']:.3f} px={px:.2f}"
    )

(root / "truth_boxes.json").write_text(
    json.dumps(truth, ensure_ascii=False, indent=2), encoding="utf-8"
)
print("wrote truth_boxes.json")
