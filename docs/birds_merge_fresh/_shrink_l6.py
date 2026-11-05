from PIL import Image
from pathlib import Path

src = Path(r"docs/birds_merge_fresh/overview_sheet_l6_fit2.png")
im = Image.open(src).convert("RGBA")
w, h = im.size
cols, rows = 3, 2
mx, my = int(w * 0.035), int(h * 0.06)
gapx, gapy = int(w * 0.02), int(h * 0.04)
cw = (w - 2 * mx - (cols - 1) * gapx) // cols
ch = (h - 2 * my - (rows - 1) * gapy) // rows

r, c = 1, 2
x0 = mx + c * (cw + gapx)
y0 = my + r * (ch + gapy)
cell = im.crop((x0, y0, x0 + cw, y0 + ch))

px = cell.load()
cw2, ch2 = cell.size
minx, miny, maxx, maxy = cw2, ch2, 0, 0
for y in range(ch2):
    for x in range(cw2):
        rr, gg, bb, aa = px[x, y]
        if aa > 10 and not (rr > 235 and gg > 235 and bb > 235):
            minx = min(minx, x)
            miny = min(miny, y)
            maxx = max(maxx, x)
            maxy = max(maxy, y)
print("bbox", minx, miny, maxx, maxy, "cell", cw2, ch2)
if maxx <= minx:
    raise SystemExit("no content")

subj = cell.crop((minx, miny, maxx + 1, maxy + 1))
pad = 0.14
max_w = int(cw2 * (1 - 2 * pad))
max_h = int(ch2 * (1 - 2 * pad))
sw, sh = subj.size
scale = min(max_w / sw, max_h / sh, 0.88)
nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
subj2 = subj.resize((nw, nh), Image.Resampling.LANCZOS)
card = Image.new("RGBA", (cw2, ch2), (255, 255, 255, 255))
ox = (cw2 - nw) // 2
oy = (ch2 - nh) // 2
card.paste(subj2, (ox, oy), subj2)
im.paste(card, (x0, y0), card)
rgb = im.convert("RGB")
outs = [
    Path(r"docs/birds_merge_fresh/overview_sheet_final.png"),
    Path(r"assets/prop/birdsmerge/overview_sheet_final.png"),
    Path(r"assets/prop/birdsmerge_fresh/overview_sheet_final.png"),
]
for p in outs:
    p.parent.mkdir(parents=True, exist_ok=True)
    rgb.save(p, "PNG")
    print("saved", p)
