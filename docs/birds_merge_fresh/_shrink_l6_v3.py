"""Shrink L6 bird by color mask (exclude white card), keep card chrome."""
from PIL import Image
from pathlib import Path
import numpy as np

src = Path(r"docs/birds_merge_fresh/overview_sheet_l6_fit3.png")
im = Image.open(src).convert("RGB")
arr = np.asarray(im).astype(np.int16)
h, w = arr.shape[:2]
cols, rows = 3, 2
cells = []
bright = (arr[:, :, 0] > 230) & (arr[:, :, 1] > 230) & (arr[:, :, 2] > 230)
for r in range(rows):
    for c in range(cols):
        x0 = int(w * c / cols)
        x1 = int(w * (c + 1) / cols)
        y0 = int(h * r / rows)
        y1 = int(h * (r + 1) / rows)
        win = bright[y0:y1, x0:x1]
        ys, xs = np.where(win)
        bx0, bx1 = int(xs.min()), int(xs.max())
        by0, by1 = int(ys.min()), int(ys.max())
        cells.append((x0 + bx0, y0 + by0, x0 + bx1, y0 + by1))

X0, Y0, X1, Y1 = cells[-1]
# compare with L5 margins: cells[-2]
LX0, LY0, LX1, LY1 = cells[-2]
card = im.crop((X0, Y0, X1 + 1, Y1 + 1))
ca = np.asarray(card).astype(np.int16)
# bird-ish: warm colors or dark eye, not white, not near-card-edge pure white
r, g, b = ca[:, :, 0], ca[:, :, 1], ca[:, :, 2]
white = (r > 232) & (g > 232) & (b > 232)
# warm yellows/oranges/browns/reds/cream
warm = ((r > 120) & (g > 60) & (b < 200) & (r + 15 >= g)) | ((r > 160) & (g < 120) & (b < 120))  # red comb
dark_eye = (r < 80) & (g < 80) & (b < 80)
mask = (warm | dark_eye) & ~white
# morphological dilate lightly via neighbors
from scipy import ndimage  # may not exist

try:
    mask = ndimage.binary_dilation(mask, iterations=2)
except Exception:
    # simple dilate
    m = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            rolled = np.roll(np.roll(mask, dy, 0), dx, 1)
            m |= rolled
    mask = m

ys, xs = np.where(mask)
print("mask pixels", mask.sum(), "bbox", xs.min(), ys.min(), xs.max(), ys.max())
pad = 3
sx0, sy0 = max(0, int(xs.min()) - pad), max(0, int(ys.min()) - pad)
sx1, sy1 = min(ca.shape[1] - 1, int(xs.max()) + pad), min(ca.shape[0] - 1, int(ys.max()) + pad)
subj_rgb = card.crop((sx0, sy0, sx1 + 1, sy1 + 1))
subj_mask = mask[sy0 : sy1 + 1, sx0 : sx1 + 1]
subj_rgba = subj_rgb.convert("RGBA")
sa = np.asarray(subj_rgba).copy()
sa[:, :, 3] = np.where(subj_mask, 255, 0).astype(np.uint8)
subj_img = Image.fromarray(sa, "RGBA")

cw, ch = card.size
# Match L5 fill: measure L5 subject
l5 = im.crop((LX0, LY0, LX1 + 1, LY1 + 1))
l5a = np.asarray(l5).astype(np.int16)
lr, lg, lb = l5a[:, :, 0], l5a[:, :, 1], l5a[:, :, 2]
l5white = (lr > 232) & (lg > 232) & (lb > 232)
l5warm = ((lr > 120) & (lg > 60) & (lb < 200) & (lr + 15 >= lg)) | ((lr > 160) & (lg < 120) & (lb < 120))
l5eye = (lr < 80) & (lg < 80) & (lb < 80)
l5m = (l5warm | l5eye) & ~l5white
ly, lx = np.where(l5m)
l5_w = lx.max() - lx.min() + 1
l5_h = ly.max() - ly.min() + 1
l5_fill = max(l5_w / l5.size[0], l5_h / l5.size[1])
print("L5 fill", round(l5_fill, 3), "L5 subj", l5_w, l5_h)

target_fill = min(0.78, l5_fill + 0.03)  # L6 can be slightly larger than L5
max_w = int(cw * target_fill)
max_h = int(ch * target_fill)
sw, sh = subj_img.size
scale = min(max_w / sw, max_h / sh)
nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
subj2 = subj_img.resize((nw, nh), Image.Resampling.LANCZOS)

# white rounded card base from original card painted white interior
base = card.convert("RGBA")
ba = np.asarray(base).copy()
# keep only near-white as card; replace all with white then paste bird
ba[:, :, :3] = 255
ba[:, :, 3] = 255
base = Image.fromarray(ba, "RGBA")
# restore soft round by using original card's white mask: where original was dark gap outside? card crop is mostly card
ox = (cw - nw) // 2
oy = (ch - nh) // 2
base.paste(subj2, (ox, oy), subj2)

out = im.convert("RGBA")
out.paste(base, (X0, Y0), base)
rgb = out.convert("RGB")
for p in [
    Path(r"docs/birds_merge_fresh/overview_sheet_final.png"),
    Path(r"assets/prop/birdsmerge/overview_sheet_final.png"),
    Path(r"assets/prop/birdsmerge_fresh/overview_sheet_final.png"),
]:
    rgb.save(p)
    print("saved", p, "scale", round(scale, 3), "nw,nh", nw, nh)
