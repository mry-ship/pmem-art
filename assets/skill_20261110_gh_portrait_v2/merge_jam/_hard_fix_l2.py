"""Hard recolor pale pink/white pith inside fruit only; protect beige plate."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parents[2]
sys.path.insert(0, str(PROJ))
from skills_kit.merge_relation import (  # noqa: E402
    _border_median,
    _cell_subject_height_ratio,
    audit_overview_sheet,
)

ASSETS = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets"
)
W, H = 720, 1280
rows, cols = 4, 2
targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.96]
max_w = [0.48, 0.58, 0.62, 0.38, 0.46, 0.56, 0.86, 0.94]


def extract_rgba(cell_arr: np.ndarray):
    h, w = cell_arr.shape[:2]
    inset = max(2, min(8, h // 40))
    work = cell_arr[inset : h - inset, inset : w - inset]
    bg = _border_median(work, band=max(1, min(4, work.shape[0] // 12)))
    diff = np.linalg.norm(work.astype(np.float32) - bg, axis=2)
    content = diff > 26
    if not content.any():
        return None
    good_rows = np.where(content.mean(axis=1) > 0.015)[0]
    good_cols = np.where(content.mean(axis=0) > 0.015)[0]
    y0, y1 = int(good_rows.min()), int(good_rows.max() + 1)
    x0, x1 = int(good_cols.min()), int(good_cols.max() + 1)
    ca = work[y0:y1, x0:x1]
    d = np.linalg.norm(ca.astype(np.float32) - bg, axis=2)
    alpha = np.clip((d - 18) / 7.0 * 255.0, 0, 255).astype(np.uint8)
    alpha = np.array(Image.fromarray(alpha).filter(ImageFilter.MedianFilter(3)))
    rgba = Image.fromarray(ca).convert("RGBA")
    rgba.putalpha(Image.fromarray(alpha))
    bbox = Image.fromarray(alpha).getbbox()
    return rgba.crop(bbox) if bbox else None


def extract_from_sheet(path: Path, idx: int):
    im = np.array(Image.open(path).convert("RGB"))
    h, w = im.shape[:2]
    r, c = divmod(idx, cols)
    y0, y1 = (h * r) // rows, (h * (r + 1)) // rows
    x0, x1 = (w * c) // cols, (w * (c + 1)) // cols
    return extract_rgba(im[y0:y1, x0:x1])


def extract_file(path: Path):
    return extract_rgba(np.array(Image.open(path).convert("RGB")))


def hard_fix(rgba: Image.Image) -> Image.Image:
    arr = np.array(rgba).astype(np.float32)
    rgb, a = arr[:, :, :3], arr[:, :, 3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = (r + g + b) / 3.0
    h, w = r.shape
    yy = np.arange(h)[:, None]
    # plate = lower ~35% with beige-ish low chroma
    plate = (yy > h * 0.62) & (np.abs(r - g) < 45) & (np.abs(g - b) < 45) & (lum > 110)
    fruit = (a > 40) & (~plate)
    # meat reference
    meat = fruit & (r > 150) & (r > g + 40) & (r > b + 25) & (lum < 200)
    target = rgb[meat].mean(axis=0) if meat.any() else np.array([205.0, 40.0, 95.0], dtype=np.float32)
    # pale / pink-white / light pink pith: high green relative OR high lum with weak chroma
    sat = (np.maximum(np.maximum(r, g), b) - np.minimum(np.minimum(r, g), b)) / np.maximum(lum, 1)
    pale = fruit & (
        ((lum > 125) & (g > 85) & (g > r * 0.52))
        | ((lum > 140) & (sat < 0.35) & (r > 120))
        | ((lum > 155) & (r > 150) & (g > 110) & ((r - g) < 70))
        | ((lum > 170) & (b > 120))
    )
    seeds = fruit & (lum < 80) & (r < 120)
    out = rgb.copy()
    # force pale to meat
    for i in range(3):
        out[:, :, i] = np.where(pale, target[i], out[:, :, i])
    # fill hollow-ish dark pits inside upper fruit (not seeds, not plate)
    hollow = fruit & (yy < h * 0.70) & (lum < 55) & (a > 100)
    rs = np.random.RandomState(11)
    if hollow.any():
        ys, xs = np.where(hollow)
        for y, x in zip(ys.tolist(), xs.tolist()):
            # keep occasional seed
            if (y + x) % 5 == 0:
                out[y, x] = np.array([65.0, 20.0, 30.0], dtype=np.float32)
            else:
                out[y, x] = np.clip(target + rs.uniform(-8, 8, 3), 0, 255)
    # protect plate pixels
    out[plate] = rgb[plate]
    out[seeds] = rgb[seeds]
    # slight magenta boost on remaining mid-pink cores
    mid = fruit & (~plate) & (~seeds) & (lum > 115) & (lum < 170) & (g > 70) & ((r - g) < 85)
    out[:, :, 0] = np.where(mid, np.clip(out[:, :, 0] + 25, 0, 255), out[:, :, 0])
    out[:, :, 1] = np.where(mid, np.clip(out[:, :, 1] * 0.55, 0, 255), out[:, :, 1])
    out[:, :, 2] = np.where(mid, np.clip(out[:, :, 2] * 0.7 + 15, 0, 255), out[:, :, 2])
    return Image.fromarray(np.dstack([out.astype(np.uint8), a.astype(np.uint8)]), "RGBA")


def score(rgba: Image.Image):
    arr = np.array(rgba.convert("RGB")).astype(np.float32)
    h, w = arr.shape[:2]
    roi = arr[int(h * 0.2) : int(h * 0.65), int(w * 0.2) : int(w * 0.8)]
    r, g, b = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    lum = (r + g + b) / 3.0
    pale = ((lum > 140) & (g > 100) & ((r - g) < 70)).mean()
    dark = (lum < 50).mean()
    mag = ((r > 150) & (r > g + 35)).mean()
    return pale, dark, mag


def main():
    candidates = [
        ASSETS / "cell_l2_inpaint_r8.jpg",
        ASSETS / "cell_l2_gummy_solid_r8.jpg",
        ASSETS / "sheet_r18b.jpg",  # will extract later if needed
        ROOT / "final.jpg",
    ]
    best = None
    best_name = ""
    best_s = 1e9
    lines = []
    for c in candidates:
        if not c.exists():
            continue
        if c.name.startswith("sheet_"):
            rgba = extract_from_sheet(c, 1)
        elif c.name == "final.jpg":
            rgba = extract_from_sheet(c, 1)
        else:
            rgba = extract_file(c)
        if rgba is None:
            continue
        fixed = hard_fix(rgba)
        pale, dark, mag = score(fixed)
        sc = pale * 4 + dark * 2 - mag * 0.5
        lines.append(f"{c.name}: pale={pale:.3f} dark={dark:.3f} mag={mag:.3f} sc={sc:.3f}")
        if sc < best_s:
            best_s, best, best_name = sc, fixed, c.name
    assert best is not None
    best.save(ROOT / "cell_l2_fixed_r8.png")
    lines.append(f"chosen={best_name}")

    cells = {i: extract_from_sheet(ROOT / "final.jpg", i) for i in range(8)}
    cells[1] = best
    out = Image.new("RGB", (W, H), (0, 0, 0))
    for i, t in enumerate(targets):
        rgba = cells[i]
        r, c = divmod(i, cols)
        y0, y1 = (H * r) // rows, (H * (r + 1)) // rows
        x0, x1 = (W * c) // cols, (W * (c + 1)) // cols
        cell_h, cell_w = y1 - y0, x1 - x0
        th = min(int(round(cell_h * t)), cell_h - 8)
        sw, sh = rgba.size
        scale = th / max(sh, 1)
        mw = int(cell_w * max_w[i])
        if sw * scale > mw:
            scale = mw / max(sw, 1)
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        if nh < int(cell_h * t * 0.97):
            nh = min(cell_h - 8, int(cell_h * t))
            nw = min(cell_w - 8, max(int(sw * (nh / max(sh, 1))), int(mw * 0.85)))
        resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        out.paste(resized, (x0 + (cell_w - nw) // 2, y0 + (cell_h - nh) // 2), resized)
        lines.append(f"L{i+1} {nw}x{nh}")
    path = ROOT / "sheet_r18.jpg"
    out.save(path, quality=95)
    out.save(ASSETS / "sheet_r18.jpg", quality=95)
    arr = np.array(out)
    Image.fromarray(arr[0 : H // 4, W // 2 : W]).save(ROOT / "l2_crop_r18_fixed.jpg", quality=95)
    hs = [
        round(
            _cell_subject_height_ratio(
                arr[(H * r) // 4 : (H * (r + 1)) // 4, (W * c) // 2 : (W * (c + 1)) // 2]
            ),
            3,
        )
        for r in range(4)
        for c in range(2)
    ]
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    text = "\n".join(lines) + f"\nheights {hs}\n" + ("PASS" if ok else "FAIL") + "\n" + "\n".join(iss) + "\n"
    (ROOT / "height_r18_composite.log").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
