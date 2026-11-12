from pathlib import Path
from PIL import Image

src = Path("assets/refs/gossip_harbor/gh_merge__ar_9x16.png")
im = Image.open(src).convert("RGB")
w, h = im.size
print("size", w, h)
board = im.crop((90, 540, 1420, 1760))
bw, bh = board.size
print("board", bw, bh)
cols, rows = 7, 9
cw, ch = bw // cols, bh // rows
out = Path("assets/skill_20261112_seafood/merge_hard_v3/gh_cells")
out.mkdir(parents=True, exist_ok=True)
for r in range(rows):
    for c in range(cols):
        cell = board.crop((c * cw + 4, r * ch + 4, (c + 1) * cw - 4, (r + 1) * ch - 4))
        cell = cell.resize((256, 256), Image.Resampling.LANCZOS)
        cell.save(out / f"cell_{r:02d}_{c:02d}.png")
strip = board.crop((0, ch * 2, bw, ch * 5))
strip.save(out / "food_strip.png")
print("saved cells + food_strip", strip.size)
