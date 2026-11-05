"""Shrink only L6 subject inside its white card with safe padding."""
from PIL import Image, ImageDraw
from pathlib import Path
import numpy as np

src = Path(r"docs/birds_merge_fresh/overview_sheet_l6_fit3.png")
im = Image.open(src).convert("RGB")
arr = np.asarray(im).astype(np.int16)
h, w = arr.shape[:2]

# Find white-ish card regions via brightness
bright = (arr[:,:,0] > 230) & (arr[:,:,1] > 230) & (arr[:,:,2] > 230)
# Rough 2x3 grid centers
cols, rows = 3, 2
cells = []
for r in range(rows):
    for c in range(cols):
        # sample center of expected cell
        cx = int(w * (c + 0.5) / cols)
        cy = int(h * (r + 0.5) / rows)
        # expand to find card bbox from this seed using bright mask flood-ish bounding
        # take a window around expected cell
        x0 = int(w * c / cols)
        x1 = int(w * (c + 1) / cols)
        y0 = int(h * r / rows)
        y1 = int(h * (r + 1) / rows)
        win = bright[y0:y1, x0:x1]
        ys, xs = np.where(win)
        if len(xs) == 0:
            raise SystemExit(f"no white in cell {r},{c}")
        # card = largest white cluster approx via bbox of white in window, then inset a bit of dark gap
        bx0, bx1 = xs.min(), xs.max()
        by0, by1 = ys.min(), ys.max()
        # convert to full image coords
        X0, Y0 = x0 + bx0, y0 + by0
        X1, Y1 = x0 + bx1, y0 + by1
        cells.append((X0, Y0, X1, Y1))
        print(f"cell{r}{c}", X0, Y0, X1, Y1, "size", X1-X0, Y1-Y0)

# L6 = last cell
X0, Y0, X1, Y1 = cells[-1]
card = im.crop((X0, Y0, X1 + 1, Y1 + 1))
ca = np.asarray(card).astype(np.int16)
# subject = not near-white
subj_mask = ~((ca[:,:,0] > 235) & (ca[:,:,1] > 235) & (ca[:,:,2] > 235))
ys, xs = np.where(subj_mask)
print("subj bbox local", xs.min(), ys.min(), xs.max(), ys.max())
pad_px = 2
sx0, sy0 = max(0, xs.min() - pad_px), max(0, ys.min() - pad_px)
sx1, sy1 = min(ca.shape[1]-1, xs.max() + pad_px), min(ca.shape[0]-1, ys.max() + pad_px)
subj = card.crop((sx0, sy0, sx1 + 1, sy1 + 1))

cw, ch = card.size
# target fill ~72% of card (match L5 feel)
max_w = int(cw * 0.72)
max_h = int(ch * 0.72)
sw, sh = subj.size
scale = min(max_w / sw, max_h / sh)
nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
subj2 = subj.resize((nw, nh), Image.Resampling.LANCZOS)

# rebuild rounded white card similar to others: fill white then paste
new_card = Image.new("RGB", (cw, ch), (255, 255, 255))
# soft round corners by copying alpha from original brightness? keep simple square; original sheet has rounded white already at sheet level
# Better: start from original card all-white painted
new_card = card.copy()
draw = ImageDraw.Draw(new_card)
# paint interior white but keep a 1px soft edge from original? fill almost all
draw.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=max(12, cw // 12), fill=(255, 255, 255))
ox = (cw - nw) // 2
oy = (ch - nh) // 2
# composite with mask from non-white of subj2
s2 = subj2.convert("RGBA")
sa = np.asarray(s2)
alpha = np.ones(sa.shape[:2], dtype=np.uint8) * 255
near_white = (sa[:,:,0] > 245) & (sa[:,:,1] > 245) & (sa[:,:,2] > 245)
alpha[near_white] = 0
s2.putalpha(Image.fromarray(alpha))
new_card_rgba = new_card.convert("RGBA")
new_card_rgba.paste(s2, (ox, oy), s2)

out = im.copy().convert("RGBA")
out.paste(new_card_rgba, (X0, Y0), new_card_rgba)
rgb = out.convert("RGB")
for p in [
    Path(r"docs/birds_merge_fresh/overview_sheet_final.png"),
    Path(r"assets/prop/birdsmerge/overview_sheet_final.png"),
    Path(r"assets/prop/birdsmerge_fresh/overview_sheet_final.png"),
]:
    rgb.save(p)
    print("saved", p, "L6 scale", round(scale, 3), "size", nw, nh, "card", cw, ch)
