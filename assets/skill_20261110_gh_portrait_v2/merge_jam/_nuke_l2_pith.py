"""Aggressively replace pale/white pith cores in L2 with solid magenta flesh+seeds."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageDraw

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
MEAT = np.array([206.0, 38.0, 92.0], dtype=np.float32)
SEED = np.array([72.0, 22.0, 34.0], dtype=np.float32)


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


def nuke_pith(rgba: Image.Image) -> Image.Image:
    """Paint solid magenta into pale cores using ellipse stamps + pixel remap."""
    arr = np.array(rgba).astype(np.float32)
    rgb, a = arr[:, :, :3].copy(), arr[:, :, 3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = (r + g + b) / 3.0
    h, w = r.shape
    yy = np.arange(h)[:, None]
    xx = np.arange(w)[None, :]

    # protect beige plate (lower band, low chroma)
    plate = (yy > h * 0.60) & (np.abs(r - g) < 50) & (np.abs(g - b) < 50) & (lum > 100) & (lum < 230)
    fruit = (a > 50) & (~plate)

    # any "too light / too pink-white" inside fruit upper body
    pale = fruit & (yy < h * 0.72) & (
        ((lum > 118) & (g > 78) & ((r - g) < 90))
        | ((lum > 135) & (g > r * 0.48))
        | ((lum > 150) & (b > 110))
        | ((lum > 125) & (r > 140) & (g > 95) & (b > 100) & ((r - g) < 80))
    )
    # also hollow dark pits in cut faces
    hollow = fruit & (yy < h * 0.70) & (lum < 60) & (a > 110)

    out = rgb.copy()
    mask = pale | hollow
    rs = np.random.RandomState(23)
    ys, xs = np.where(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if (y * 3 + x) % 6 == 0:
            out[y, x] = SEED + rs.uniform(-6, 6, 3)
        else:
            # slight radial darkening toward edge of pale region
            out[y, x] = np.clip(MEAT + rs.uniform(-14, 10, 3), 0, 255)

    # stamp two solid magenta ellipses over likely left/right cut centers
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # left and right berry cut centers (empirical for dish compositions)
    centers = [
        (int(w * 0.36), int(h * 0.42), int(w * 0.12), int(h * 0.16)),
        (int(w * 0.64), int(h * 0.42), int(w * 0.12), int(h * 0.16)),
    ]
    for cx, cy, rx, ry in centers:
        bbox = [cx - rx, cy - ry, cx + rx, cy + ry]
        draw.ellipse(bbox, fill=(int(MEAT[0]), int(MEAT[1]), int(MEAT[2]), 210))
        # seed speckles
        for _ in range(28):
            sx = int(cx + rs.uniform(-rx * 0.7, rx * 0.7))
            sy = int(cy + rs.uniform(-ry * 0.7, ry * 0.7))
            if 0 <= sx < w and 0 <= sy < h:
                draw.ellipse([sx - 1, sy - 1, sx + 1, sy + 1], fill=(70, 22, 34, 230))

    ov = np.array(overlay).astype(np.float32)
    oa = (ov[:, :, 3] / 255.0)[..., None]
    # only apply overlay where fruit & not plate & (pale-ish or inside ellipse alpha)
    apply = fruit & (yy < h * 0.68)
    apply3 = apply[..., None]
    blended = out * (1 - oa) + ov[:, :, :3] * oa
    out = np.where(apply3 & (oa > 0.05), blended, out)

    # final pass: remaining pale
    r2, g2, b2 = out[:, :, 0], out[:, :, 1], out[:, :, 2]
    lum2 = (r2 + g2 + b2) / 3.0
    still = fruit & (yy < h * 0.70) & (lum2 > 130) & (g2 > 90) & ((r2 - g2) < 85)
    out[still] = MEAT
    # sprinkle seeds on still
    sy2, sx2 = np.where(still)
    for y, x in list(zip(sy2.tolist(), sx2.tolist()))[::5]:
        out[y, x] = SEED

    out[plate] = rgb[plate]
    return Image.fromarray(np.dstack([np.clip(out, 0, 255).astype(np.uint8), a.astype(np.uint8)]), "RGBA")


def score(rgba: Image.Image):
    arr = np.array(rgba.convert("RGB")).astype(np.float32)
    h, w = arr.shape[:2]
    roi = arr[int(h * 0.25) : int(h * 0.58), int(w * 0.22) : int(w * 0.78)]
    r, g, b = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
    lum = (r + g + b) / 3.0
    pale = ((lum > 135) & (g > 95) & ((r - g) < 80)).mean()
    dark = (lum < 48).mean()
    mag = ((r > 155) & (r > g + 40)).mean()
    return pale, dark, mag


def main():
    cands = [
        ASSETS / "cell_l2_solid_r8e.jpg",
        ASSETS / "cell_l2_inpaint_r8.jpg",
        ASSETS / "cell_l2_gummy_solid_r8.jpg",
        ROOT / "final.jpg",
    ]
    best = None
    best_name = ""
    best_sc = 1e9
    lines = []
    for c in cands:
        if not c.exists():
            continue
        rgba = extract_from_sheet(c, 1) if c.name == "final.jpg" else extract_file(c)
        if rgba is None:
            continue
        fixed = nuke_pith(rgba)
        pale, dark, mag = score(fixed)
        sc = pale * 5 + dark * 1.5 - mag * 0.5
        lines.append(f"{c.name}: pale={pale:.3f} dark={dark:.3f} mag={mag:.3f} sc={sc:.3f}")
        if sc < best_sc:
            best_sc, best, best_name = sc, fixed, c.name

    assert best is not None
    best.save(ROOT / "cell_l2_fixed_r8.png")
    lines.append(f"chosen={best_name} sc={best_sc:.3f}")

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
                arr[(H * rr) // 4 : (H * (rr + 1)) // 4, (W * cc) // 2 : (W * (cc + 1)) // 2]
            ),
            3,
        )
        for rr in range(4)
        for cc in range(2)
    ]
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    text = "\n".join(lines) + f"\nheights {hs}\n" + ("PASS" if ok else "FAIL") + "\n" + "\n".join(iss)
    (ROOT / "height_r18_composite.log").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
