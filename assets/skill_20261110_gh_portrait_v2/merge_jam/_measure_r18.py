from pathlib import Path
import sys
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parents[2]
sys.path.insert(0, str(PROJ))
from skills_kit.merge_relation import _cell_subject_height_ratio, audit_overview_sheet
src = ROOT / "sheet_r18_gen.jpg"
if not src.exists():
    src = Path(
        r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets\sheet_r18.jpg"
    )
arr = np.array(Image.open(src).convert("RGB"))
H, W = arr.shape[:2]
# crop L2 for inspection
r, c = 0, 1
y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
Image.fromarray(arr[y0:y1, x0:x1]).save(ROOT / "l2_crop_r18.jpg", quality=95)
hs = []
for rr in range(4):
    yy0, yy1 = (H * rr) // 4, (H * (rr + 1)) // 4
    for cc in range(2):
        xx0, xx1 = (W * cc) // 2, (W * (cc + 1)) // 2
        hs.append(round(_cell_subject_height_ratio(arr[yy0:yy1, xx0:xx1]), 3))
ok, iss = audit_overview_sheet(src, rows=4, cols=2)
(ROOT / "height_r18.log").write_text(
    f"src {src}\nok {ok}\nheights {hs}\nmsgs {iss}\n", encoding="utf-8"
)
print("src", src)
print("ok", ok)
print("heights", hs)
print("msgs", iss)
