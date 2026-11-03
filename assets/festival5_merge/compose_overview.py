# -*- coding: utf-8 -*-
"""Compose 5 tracks x L1-L6 into one overview sheet."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
TRACKS = [
    ("prize", "Prize 奖牌"),
    ("balloon", "Balloon 气球"),
    ("candy", "Candy 糖球"),
    ("magic", "Magic 星球"),
    ("box", "Box 福袋"),
]
LEVELS = list(range(1, 7))
CELL = 220
PAD = 16
LABEL_W = 160
HEADER_H = 48
ROW_GAP = 12
COL_GAP = 12
BG = (18, 22, 30, 255)
PANEL = (28, 36, 48, 255)
TEXT = (232, 238, 246, 255)
MUTED = (147, 164, 184, 255)


def load_cell(track: str, level: int) -> Image.Image:
    p = ROOT / track / f"L{level:02d}.png"
    im = Image.open(p).convert("RGBA")
    # fit into CELL box keeping aspect
    im.thumbnail((CELL - 12, CELL - 12), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    x = (CELL - im.width) // 2
    y = (CELL - im.height) // 2
    canvas.paste(im, (x, y), im)
    return canvas


def main() -> None:
    cols = len(LEVELS)
    rows = len(TRACKS)
    w = PAD * 2 + LABEL_W + cols * CELL + (cols - 1) * COL_GAP
    h = PAD * 2 + HEADER_H + rows * CELL + (rows - 1) * ROW_GAP + 36
    sheet = Image.new("RGBA", (w, h), BG)
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("msyh.ttc", 20)
        font_sm = ImageFont.truetype("msyh.ttc", 16)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font

    draw.text((PAD, PAD), "Festival Merge · 五链升级总览 L1–L6", fill=TEXT, font=font)

    # column headers
    for i, lv in enumerate(LEVELS):
        x = PAD + LABEL_W + i * (CELL + COL_GAP)
        draw.text((x + CELL // 2 - 12, PAD + 28), f"L{lv}", fill=MUTED, font=font_sm)

    for r, (track, title) in enumerate(TRACKS):
        y = PAD + HEADER_H + r * (CELL + ROW_GAP)
        # label
        draw.rounded_rectangle(
            (PAD, y, PAD + LABEL_W - 8, y + CELL),
            radius=12,
            fill=PANEL,
        )
        draw.text((PAD + 14, y + CELL // 2 - 10), title, fill=TEXT, font=font_sm)
        for c, lv in enumerate(LEVELS):
            x = PAD + LABEL_W + c * (CELL + COL_GAP)
            draw.rounded_rectangle((x, y, x + CELL, y + CELL), radius=16, fill=PANEL)
            cell = load_cell(track, lv)
            sheet.alpha_composite(cell, (x, y))

    out = ROOT / "overview_L1_L6.png"
    sheet.convert("RGB").save(out, "PNG", optimize=True)
    print(out)

    # also write simple HTML
    html = ROOT / "overview.html"
    cells = []
    for track, title in TRACKS:
        imgs = "".join(
            f'<figure><img src="{track}/L{lv:02d}.png" alt="{track} L{lv}"><figcaption>L{lv}</figcaption></figure>'
            for lv in LEVELS
        )
        cells.append(f'<section><h2>{title}</h2><div class="row">{imgs}</div></section>')
    html.write_text(
        """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Festival5 Merge Overview</title>
<style>
body{margin:0;background:#12161e;color:#e8eef6;font-family:"Segoe UI","Microsoft YaHei",sans-serif;padding:20px}
h1{font-size:20px;margin:0 0 8px}h2{font-size:15px;margin:18px 0 8px;color:#93a4b8}
.row{display:flex;gap:10px;flex-wrap:wrap}
figure{margin:0;background:#1c2430;border-radius:12px;padding:8px;text-align:center}
img{width:140px;height:140px;object-fit:contain;display:block}
figcaption{font-size:12px;color:#93a4b8;margin-top:4px}
.board{margin-top:16px} .board img{width:min(100%,1100px);height:auto;border-radius:12px}
</style></head><body>
<h1>Festival Merge · 五链升级总览 L1–L6</h1>
<p>单件分格交付；下方为同页总览拼图。</p>
"""
        + "\n".join(cells)
        + '<div class="board"><h2>同页总览</h2><img src="overview_L1_L6.png" alt="overview"></div></body></html>',
        encoding="utf-8",
    )
    print(html)


if __name__ == "__main__":
    main()
