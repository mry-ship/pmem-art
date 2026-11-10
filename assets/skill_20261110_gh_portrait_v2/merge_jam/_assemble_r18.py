"""Assemble sheet_r18: final cells + best solid L2 (gummy preferred), height ladder locked."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parents[2]
sys.path.insert(0, str(PROJ))
ASSETS_CURSOR = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets"
)
ERR = ROOT / "_assemble_r18_err.txt"

try:
    from skills_kit.merge_relation import (
        _border_median,
        _cell_subject_height_ratio,
        audit_overview_sheet,
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

    def score_l2(rgba: Image.Image) -> tuple[float, float, float]:
        arr = np.array(rgba.convert("RGB")).astype(np.float32)
        h, w = arr.shape[:2]
        roi = arr[int(h * 0.28) : int(h * 0.72), int(w * 0.22) : int(w * 0.78)]
        r, g, b = roi[:, :, 0], roi[:, :, 1], roi[:, :, 2]
        lum = (r + g + b) / 3.0
        pale = ((lum > 150) & (r > 140) & (g > 110) & ((r - g) < 55)).mean()
        dark = (lum < 50).mean()
        magenta = ((r > 140) & (r > g + 30) & (r > b + 15)).mean()
        # lower is better for pale+dark; higher magenta better
        return float(pale), float(dark), float(magenta)

    def recolor_pith(rgba: Image.Image) -> Image.Image:
        arr = np.array(rgba).astype(np.float32)
        rgb = arr[:, :, :3]
        a = arr[:, :, 3]
        r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
        lum = (r + g + b) / 3.0
        pale = (
            (lum > 130)
            & (r > 140)
            & (g > 100)
            & (b > 100)
            & ((r - g) < 55)
            & ((r - b) < 55)
            & (a > 40)
        )
        meat = (r > 145) & (r > g + 35) & (r > b + 20) & (a > 40) & (~pale)
        target = rgb[meat].mean(axis=0) if meat.any() else np.array([200.0, 42.0, 90.0], dtype=np.float32)
        seeds = (lum < 85) & (a > 40)
        out = rgb.copy()
        out[:, :, 0] = np.where(pale, np.clip(target[0] * 0.9 + r * 0.1, 0, 255), out[:, :, 0])
        out[:, :, 1] = np.where(pale, np.clip(target[1] * 0.85 + g * 0.15, 0, 255), out[:, :, 1])
        out[:, :, 2] = np.where(pale, np.clip(target[2] * 0.85 + b * 0.15, 0, 255), out[:, :, 2])
        # fill dark cavities that look like hollow cores (not seeds)
        hollow = (lum < 48) & (a > 90)
        if hollow.any():
            yy, xx = np.where(hollow)
            rs = np.random.RandomState(7)
            for y, x in zip(yy.tolist(), xx.tolist()):
                y0, y1 = max(0, y - 3), min(out.shape[0], y + 4)
                x0, x1 = max(0, x - 3), min(out.shape[1], x + 4)
                neigh = rgb[y0:y1, x0:x1]
                nr = float(neigh[:, :, 0].mean())
                ng = float(neigh[:, :, 1].mean())
                # fill only if surrounded by reddish fruit
                if nr > ng + 20 and nr > 90:
                    noise = rs.uniform(-10, 10, 3)
                    out[y, x] = np.clip(target + noise, 0, 255)
                    if (y + x) % 6 == 0:
                        out[y, x] = np.array([68.0, 22.0, 34.0], dtype=np.float32)
        out[seeds] = rgb[seeds]
        return Image.fromarray(np.dstack([out.astype(np.uint8), a.astype(np.uint8)]), "RGBA")

    final = ROOT / "final.jpg"
    candidates = [
        ASSETS_CURSOR / "cell_l2_gummy_solid_r8.jpg",
        ROOT / "cell_l2_gummy_solid_r8.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8d.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8c.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8b.jpg",
        ASSETS_CURSOR / "cell_l2_fullflesh_r8.jpg",
        ROOT / "cell_l2_fixed_r8.png",
    ]
    best = None
    best_key = None
    best_score = 1e9
    for c in candidates:
        if not c.exists():
            continue
        rgba = extract_file(c)
        if rgba is None:
            continue
        fixed = recolor_pith(rgba)
        pale, dark, magenta = score_l2(fixed)
        # penalize pale and dark hollow; reward magenta
        score = pale * 3.0 + dark * 2.0 - magenta * 0.4
        log.append(f"{c.name}: pale={pale:.3f} dark={dark:.3f} mag={magenta:.3f} score={score:.3f}")
        if score < best_score:
            best_score = score
            best = fixed
            best_key = c.name

    if best is None:
        best = recolor_pith(extract_from_sheet(final, 1))
        best_key = "final_recolor"
    best.save(ROOT / "cell_l2_fixed_r8.png")
    log.append(f"chosen={best_key} score={best_score:.3f}")

    cells = {i: extract_from_sheet(final, i) for i in range(8)}
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
        px = x0 + (cell_w - nw) // 2
        py = y0 + (cell_h - nh) // 2
        out.paste(resized, (px, py), resized)
        log.append(f"L{i+1} {nw}x{nh}")

    path = ROOT / "sheet_r18.jpg"
    out.save(path, quality=95)
    out.save(ASSETS_CURSOR / "sheet_r18.jpg", quality=95)
    arr2 = np.array(out)
    Image.fromarray(arr2[0 : H // 4, W // 2 : W]).save(ROOT / "l2_crop_r18_fixed.jpg", quality=95)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(round(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]), 3))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    (ROOT / "height_r18_composite.log").write_text(
        "\n".join(log) + f"\nheights {hs}\n" + ("PASS" if ok else "FAIL") + "\n" + "\n".join(iss) + "\n",
        encoding="utf-8",
    )
    print("ok", ok)
    print("heights", hs)
    print("chosen", best_key)
except Exception:
    ERR.write_text(traceback.format_exc(), encoding="utf-8")
    raise
