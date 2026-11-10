"""Recolor pale/white pith in final L2 to solid magenta flesh; keep seeds/dark."""
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

ASSETS_CURSOR = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets"
)

W, H = 720, 1280
rows, cols = 4, 2
targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.96]
max_w = [0.48, 0.58, 0.62, 0.38, 0.46, 0.56, 0.86, 0.94]
log: list[str] = []


def extract_rgba(cell_arr: np.ndarray):
    h, w = cell_arr.shape[:2]
    inset = max(2, min(8, h // 40))
    work = cell_arr[inset : h - inset, inset : w - inset]
    bg = _border_median(work, band=max(1, min(4, work.shape[0] // 12)))
    diff = np.linalg.norm(work.astype(np.float32) - bg, axis=2)
    content = diff > 26
    if not content.any():
        return None
    row_d = content.mean(axis=1)
    col_d = content.mean(axis=0)
    good_rows = np.where(row_d > 0.015)[0]
    good_cols = np.where(col_d > 0.015)[0]
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


def extract_from_sheet(sheet_path: Path, idx: int):
    im = np.array(Image.open(sheet_path).convert("RGB"))
    h, w = im.shape[:2]
    r, c = divmod(idx, cols)
    y0, y1 = (h * r) // rows, (h * (r + 1)) // rows
    x0, x1 = (w * c) // cols, (w * (c + 1)) // cols
    return extract_rgba(im[y0:y1, x0:x1])


def extract_file(path: Path):
    return extract_rgba(np.array(Image.open(path).convert("RGB")))


def recolor_pith(rgba: Image.Image) -> Image.Image:
    arr = np.array(rgba).astype(np.float32)
    rgb = arr[:, :, :3]
    a = arr[:, :, 3]
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    lum = (r + g + b) / 3.0
    # pale / white / light pink pith (not plate beige which is outside fruit)
    # fruit region: reddish dominant OR high-sat magenta nearby; pith is light & low chroma
    pale = (
        (lum > 150)
        & (r > 140)
        & (g > 110)
        & (b > 110)
        & ((r - g) < 55)
        & (a > 40)
    )
    # also mid pale pink cores
    pale2 = (
        (lum > 130)
        & (lum < 210)
        & (r > 150)
        & (g > 100)
        & (b > 110)
        & ((r - g) < 45)
        & ((r - b) < 50)
        & (a > 40)
    )
    mask = pale | pale2
    # protect plate: very low chroma beige with g~b and outside fruit cluster — already mostly outside
    # target flesh color from surrounding magenta meat
    meat = (r > 140) & (r > g + 35) & (r > b + 20) & (a > 40) & (~mask)
    if meat.any():
        target = rgb[meat].mean(axis=0)
    else:
        target = np.array([196.0, 48.0, 88.0], dtype=np.float32)
    # slight variation with seed speckles kept if dark
    seeds = (lum < 90) & (a > 40)
    out = rgb.copy()
    # blend pale toward meat
    for ch in range(3):
        out[:, :, ch] = np.where(mask, target[ch] * 0.82 + rgb[:, :, ch] * 0.18, out[:, :, ch])
    # push a bit more magenta on pale2
    out[:, :, 0] = np.where(mask, np.clip(out[:, :, 0] + 18, 0, 255), out[:, :, 0])
    out[:, :, 1] = np.where(mask, np.clip(out[:, :, 1] * 0.55, 0, 255), out[:, :, 1])
    out[:, :, 2] = np.where(mask, np.clip(out[:, :, 2] * 0.75 + 10, 0, 255), out[:, :, 2])
    # keep seeds
    out[seeds] = rgb[seeds]
    # fill near-black hollow cavities inside fruit bbox with meat color + seed noise
    # detect dark holes surrounded by fruit (not background: a already cropped)
    hollow = (lum < 55) & (a > 80) & (~seeds)
    # only fill if neighbors are reddish (inside fruit)
    if hollow.any():
        yy, xx = np.where(hollow)
        for y, x in zip(yy.tolist(), xx.tolist()):
            y0, y1 = max(0, y - 2), min(out.shape[0], y + 3)
            x0, x1 = max(0, x - 2), min(out.shape[1], x + 3)
            neigh = rgb[y0:y1, x0:x1]
            nr = neigh[:, :, 0].mean()
            ng = neigh[:, :, 1].mean()
            if nr > ng + 25 and nr > 100:
                noise = np.random.RandomState(y * 1000 + x).uniform(-12, 12, 3)
                out[y, x] = np.clip(target + noise, 0, 255)
                # occasional seed
                if (y + x) % 7 == 0:
                    out[y, x] = np.array([70, 25, 35], dtype=np.float32)
    rgba2 = np.dstack([out.astype(np.uint8), a.astype(np.uint8)])
    return Image.fromarray(rgba2, "RGBA")


def main():
    final = ROOT / "final.jpg"
    # prefer best generated L2 if available and less pale
    candidates = [
        ASSETS_CURSOR / "cell_l2_fullflesh_r8d.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8c.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8b.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8.jpg",
    ]
    l2 = None
    source = "final_recolor"
    for c in candidates:
        if not c.exists():
            continue
        rgba = extract_file(c)
        if rgba is None:
            continue
        arr = np.array(rgba.convert("RGB")).astype(np.float32)
        roi = arr[int(arr.shape[0] * 0.3) : int(arr.shape[0] * 0.7), int(arr.shape[1] * 0.25) : int(arr.shape[1] * 0.75)]
        pale = (
            ((roi.mean(axis=2) > 150) & (roi[:, :, 0] > 140) & (roi[:, :, 1] > 110) & ((roi[:, :, 0] - roi[:, :, 1]) < 55)).mean()
        )
        dark = (roi.mean(axis=2) < 50).mean()
        log.append(f"cand {c.name} pale={pale:.3f} dark={dark:.3f}")
        # prefer low pale AND low dark (solid magenta)
        if pale < 0.04 and dark < 0.12:
            l2 = recolor_pith(rgba)
            source = c.name
            break
    if l2 is None:
        base = extract_from_sheet(final, 1)
        l2 = recolor_pith(base)
        source = "final_recolor"
    l2.save(ROOT / "cell_l2_fixed_r8.png")
    log.append(f"L2 source={source}")

    cells = {i: extract_from_sheet(final, i) for i in range(8)}
    cells[1] = l2
    out = Image.new("RGB", (W, H), (0, 0, 0))
    for i, t in enumerate(targets):
        rgba = cells[i]
        if rgba is None:
            log.append(f"FAIL L{i+1}")
            continue
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
        px = x0 + (cell_w - nw) // 2
        py = y0 + (cell_h - nh) // 2
        out.paste(resized, (px, py), resized)
        log.append(f"L{i+1} {nw}x{nh}")

    path = ROOT / "sheet_r18.jpg"
    out.save(path, quality=95)
    out.save(ASSETS_CURSOR / "sheet_r18.jpg", quality=95)
    # also overwrite gen name consistency
    arr2 = np.array(out)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(round(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]), 3))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    # crop fixed L2 for review
    Image.fromarray(arr2[0 : H // 4, W // 2 : W]).save(ROOT / "l2_crop_r18_fixed.jpg", quality=95)
    (ROOT / "height_r18_composite.log").write_text(
        "\n".join(log)
        + f"\nheights {hs}\n"
        + ("PASS" if ok else "FAIL")
        + "\n"
        + "\n".join(iss)
        + "\n",
        encoding="utf-8",
    )
    print("ok", ok)
    print("heights", hs)
    print("source", source)
    print("\n".join(iss))


if __name__ == "__main__":
    main()
