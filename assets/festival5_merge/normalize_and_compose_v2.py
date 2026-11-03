# -*- coding: utf-8 -*-
"""Import Cursor gens, force scale_pct occupancy, compose overview."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
SRC = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")
CANVAS = 1024
SCALE = {
    1: 0.58,
    2: 0.62,
    3: 0.66,
    4: 0.70,
    5: 0.74,
    6: 0.78,
}
TRACKS = [
    ("prize", "Prize 奖牌"),
    ("balloon", "Balloon 气球"),
    ("candy", "Candy 糖球"),
    ("magic", "Magic 星球"),
    ("box", "Box 福袋"),
]


def alpha_bbox(im: Image.Image, thr: int = 8):
    a = im.split()[-1]
    bb = a.point(lambda p: 255 if p > thr else 0).getbbox()
    return bb


def to_rgba(path: Path) -> Image.Image:
    im = Image.open(path).convert("RGBA")
    # if near-black background, punch to transparent for nicer compose
    px = im.load()
    w, h = im.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 0 and r < 18 and g < 18 and b < 18:
                px[x, y] = (r, g, b, 0)
    return im


def fit_to_scale(src: Image.Image, scale_pct: float) -> Image.Image:
    im = src.convert("RGBA")
    bb = alpha_bbox(im)
    if not bb:
        bb = im.getbbox() or (0, 0, im.width, im.height)
    cropped = im.crop(bb)
    target = int(CANVAS * scale_pct)
    # fit longest side to target
    cw, ch = cropped.size
    longest = max(cw, ch)
    ratio = target / max(longest, 1)
    nw, nh = max(1, int(cw * ratio)), max(1, int(ch * ratio))
    resized = cropped.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(resized, ((CANVAS - nw) // 2, (CANVAS - nh) // 2), resized)
    return canvas


def import_all() -> None:
    for track, _ in TRACKS:
        # L01 from existing player asset
        l01 = ROOT / track / "L01.png"
        out01 = fit_to_scale(to_rgba(l01), SCALE[1])
        out01.save(ROOT / track / "L01.png")
        for lv in range(2, 7):
            src = SRC / f"festival5_{track}_L{lv:02d}.jpg"
            if not src.exists():
                raise FileNotFoundError(src)
            fitted = fit_to_scale(to_rgba(src), SCALE[lv])
            fitted.save(ROOT / track / f"L{lv:02d}.png")
            print("wrote", track, f"L{lv:02d}", "pct", SCALE[lv])


def compose() -> Path:
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
    levels = list(range(1, 7))
    w = PAD * 2 + LABEL_W + len(levels) * CELL + (len(levels) - 1) * COL_GAP
    h = PAD * 2 + HEADER_H + len(TRACKS) * CELL + (len(TRACKS) - 1) * ROW_GAP + 36
    sheet = Image.new("RGBA", (w, h), BG)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((PAD, PAD), "Festival Merge v2 L1-L6 (Cursor gen + scale lock)", fill=TEXT, font=font)
    for i, lv in enumerate(levels):
        x = PAD + LABEL_W + i * (CELL + COL_GAP)
        draw.text((x + CELL // 2 - 10, PAD + 28), f"L{lv}", fill=MUTED, font=font)
    for r, (track, title) in enumerate(TRACKS):
        y = PAD + HEADER_H + r * (CELL + ROW_GAP)
        draw.rounded_rectangle((PAD, y, PAD + LABEL_W - 8, y + CELL), radius=12, fill=PANEL)
        draw.text((PAD + 14, y + CELL // 2 - 6), title.split()[0], fill=TEXT, font=font)
        for c, lv in enumerate(levels):
            x = PAD + LABEL_W + c * (CELL + COL_GAP)
            draw.rounded_rectangle((x, y, x + CELL, y + CELL), radius=16, fill=PANEL)
            im = Image.open(ROOT / track / f"L{lv:02d}.png").convert("RGBA")
            im.thumbnail((CELL - 12, CELL - 12), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
            canvas.paste(im, ((CELL - im.width) // 2, (CELL - im.height) // 2), im)
            sheet.alpha_composite(canvas, (x, y))
    out = ROOT / "overview_L1_L6.png"
    sheet.convert("RGB").save(out, "PNG", optimize=True)
    print("overview", out, out.stat().st_size)
    return out


if __name__ == "__main__":
    import_all()
    compose()
