"""Force L2 from solid_r8e: fill hollow cavities completely with magenta flesh+seeds."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

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
MEAT = np.array([210.0, 36.0, 96.0], dtype=np.float32)
SEED = np.array([68.0, 20.0, 32.0], dtype=np.float32)


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


def fill_solid(rgba: Image.Image) -> Image.Image:
    arr = np.array(rgba).astype(np.float32)
    rgb, a = arr[:, :, :3].copy(), arr[:, :, 3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = (r + g + b) / 3.0
    h, w = r.shape
    yy = np.arange(h)[:, None]
    plate = (yy > h * 0.62) & (np.abs(r - g) < 55) & (np.abs(g - b) < 55) & (lum > 105)
    fruit = (a > 40) & (~plate)
    out = rgb.copy()

    # stamp large solid ellipses over both cut centers (fill hollow + any pale)
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ov)
    rs = np.random.RandomState(42)
    for cx, cy, rx, ry in [
        (int(w * 0.34), int(h * 0.40), int(w * 0.16), int(h * 0.18)),
        (int(w * 0.66), int(h * 0.40), int(w * 0.16), int(h * 0.18)),
    ]:
        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=(210, 36, 96, 235))
        for _ in range(40):
            sx = int(cx + rs.uniform(-rx * 0.75, rx * 0.75))
            sy = int(cy + rs.uniform(-ry * 0.75, ry * 0.75))
            if 0 <= sx < w and 0 <= sy < h:
                rad = 1 if (sx + sy) % 3 else 2
                draw.ellipse([sx - rad, sy - rad, sx + rad, sy + rad], fill=(68, 20, 32, 245))
    ova = np.array(ov).astype(np.float32)
    oa = (ova[:, :, 3] / 255.0)[..., None]
    apply = fruit & (yy < h * 0.70)
    out = np.where(apply[..., None] & (oa > 0.08), out * (1 - oa) + ova[:, :, :3] * oa, out)

    # remount: kill remaining pale / hollow in fruit body
    r2, g2, b2 = out[:, :, 0], out[:, :, 1], out[:, :, 2]
    lum2 = (r2 + g2 + b2) / 3.0
    bad = fruit & (yy < h * 0.68) & (
        ((lum2 > 110) & (g2 > 70) & ((r2 - g2) < 95))
        | ((lum2 < 70) & (a > 100))  # hollow shadow pits
    )
    ys, xs = np.where(bad)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if (y + x * 2) % 5 == 0:
            out[y, x] = SEED + rs.uniform(-5, 5, 3)
        else:
            out[y, x] = np.clip(MEAT + rs.uniform(-12, 8, 3), 0, 255)

    out[plate] = rgb[plate]
    return Image.fromarray(
        np.dstack([np.clip(out, 0, 255).astype(np.uint8), a.astype(np.uint8)]), "RGBA"
    )


def main():
    src = ASSETS / "cell_l2_solid_r8e.jpg"
    rgba = extract_file(src)
    fixed = fill_solid(rgba)
    fixed.save(ROOT / "cell_l2_fixed_r8.png")
    # also save RGB preview
    fixed.convert("RGB").save(ROOT / "cell_l2_fixed_r8_preview.jpg", quality=95)

    cells = {i: extract_from_sheet(ROOT / "final.jpg", i) for i in range(8)}
    cells[1] = fixed
    out = Image.new("RGB", (W, H), (0, 0, 0))
    log = [f"L2 from {src.name} hollow-filled"]
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
        log.append(f"L{i+1} {nw}x{nh}")

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
    text = "\n".join(log) + f"\nheights {hs}\n" + ("PASS" if ok else "FAIL") + "\n" + "\n".join(iss)
    (ROOT / "height_r18_composite.log").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
