from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
pairs = [
    ("final_L2", np.array(Image.open(ROOT / "final.jpg").convert("RGB")), True),
    ("fixed_crop", np.array(Image.open(ROOT / "l2_crop_r18_fixed.jpg").convert("RGB")), False),
    ("fixed_cell", np.array(Image.open(ROOT / "cell_l2_fixed_r8.png").convert("RGBA")), False),
]
lines = []
for name, im, is_sheet in pairs:
    if is_sheet:
        h, w = im.shape[:2]
        cell = im[0 : h // 4, w // 2 : w]
    else:
        cell = im[:, :, :3] if im.shape[-1] == 4 else im
    ch, cw = cell.shape[:2]
    # center of cut faces roughly
    patches = [
        ("cL", cell[int(ch * 0.40) : int(ch * 0.55), int(cw * 0.30) : int(cw * 0.42)]),
        ("cR", cell[int(ch * 0.40) : int(ch * 0.55), int(cw * 0.58) : int(cw * 0.70)]),
    ]
    for pn, p in patches:
        mean = p.mean(axis=(0, 1))
        lines.append(f"{name}.{pn} meanRGB={mean.round(1).tolist()} lum={mean.mean():.1f} r-g={mean[0]-mean[1]:.1f}")
    Image.fromarray(cell).save(ROOT / f"_cmp_{name}.jpg", quality=95)

(ROOT / "l2_compare.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
