"""Rescale wind ladder cells to strict ascending subject heights."""
from pathlib import Path
import sys
import traceback

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
ERR = ROOT / "_make_r15_err.txt"

try:
    from PIL import Image, ImageFilter, ImageEnhance
    import numpy as np
    from skills_kit.merge_relation import (
        _cell_subject_height_ratio,
        audit_overview_sheet,
        _border_median,
    )

    final = np.array(Image.open(ROOT / "final.jpg").convert("RGB"))
    r13 = np.array(Image.open(ROOT / "sheet_r13.jpg").convert("RGB"))
    H, W = final.shape[:2]
    rows, cols = 4, 2
    targets = [0.38, 0.46, 0.54, 0.62, 0.70, 0.78, 0.86, 0.96]
    # Prefer r13 for L4 (fatter keys); final for identity elsewhere.
    src_pick = [final, final, final, r13, final, final, final, final]
    max_w_frac = [0.42, 0.38, 0.40, 0.78, 0.88, 0.72, 0.86, 0.94]
    out = Image.new("RGB", (W, H), (0, 0, 0))
    log = []

    def cell_box(i):
        r, c = divmod(i, cols)
        y0, y1 = (H * r) // rows, (H * (r + 1)) // rows
        x0, x1 = (W * c) // cols, (W * (c + 1)) // cols
        return y0, y1, x0, x1

    def extract(cell_arr, strip_side_rails=False):
        h, w = cell_arr.shape[:2]
        inset = 4
        work = cell_arr[inset : h - inset, inset : w - inset].copy()
        bg = _border_median(work, band=max(1, min(4, work.shape[0] // 12)))
        diff = np.linalg.norm(work.astype(np.float32) - bg, axis=2)
        content = diff > 28
        if not content.any():
            return None
        if strip_side_rails:
            # Drop tall thin green side pillars / back rails near left/right edges.
            wh, ww = work.shape[:2]
            rgb = work.astype(np.float32)
            green = (rgb[:, :, 1] > rgb[:, :, 0] + 18) & (rgb[:, :, 1] > rgb[:, :, 2] + 12)
            # Keep keyboard/base greens: only remove upper lateral rails.
            upper = np.zeros_like(green)
            upper[: int(wh * 0.72), :] = True
            left = np.zeros_like(green)
            right = np.zeros_like(green)
            left[:, : int(ww * 0.18)] = True
            right[:, int(ww * 0.82) :] = True
            rail = green & upper & (left | right) & content
            # also thin vertical green bands beside pipes
            col_green = (green & content).mean(axis=0)
            for x in range(ww):
                if col_green[x] > 0.35 and (x < ww * 0.22 or x > ww * 0.78):
                    rail[:, x] = rail[:, x] | (green[:, x] & upper[:, x] & content[:, x])
            work = work.copy()
            work[rail] = bg.astype(np.uint8)
            # fill small holes with nearby cream by blurring mask edge
            content = (~rail) & (diff > 28)

        ys, xs = np.where(content)
        y0, y1 = int(ys.min()), int(ys.max() + 1)
        x0, x1 = int(xs.min()), int(xs.max() + 1)
        row_d = content.mean(axis=1)
        col_d = content.mean(axis=0)
        good_rows = np.where(row_d > 0.015)[0]
        good_cols = np.where(col_d > 0.015)[0]
        if len(good_rows) and len(good_cols):
            y0, y1 = int(good_rows.min()), int(good_rows.max() + 1)
            x0, x1 = int(good_cols.min()), int(good_cols.max() + 1)
        pad = 2
        y0 = max(0, y0 - pad)
        x0 = max(0, x0 - pad)
        y1 = min(work.shape[0], y1 + pad)
        x1 = min(work.shape[1], x1 + pad)
        ca = work[y0:y1, x0:x1]
        d = np.linalg.norm(ca.astype(np.float32) - bg, axis=2)
        alpha = np.clip((d - 18) / 10.0 * 255.0, 0, 255).astype(np.uint8)
        alpha = np.array(Image.fromarray(alpha).filter(ImageFilter.MedianFilter(3)))
        rgba = Image.fromarray(ca).convert("RGBA")
        rgba.putalpha(Image.fromarray(alpha))
        bbox = Image.fromarray(alpha).getbbox()
        if not bbox:
            return None
        return rgba.crop(bbox)

    def boost_l4_keys(rgba):
        # Mild local contrast so mushroom keys read more bulbous after downscale.
        rgb = rgba.convert("RGB")
        rgb = ImageEnhance.Contrast(rgb).enhance(1.08)
        rgb = ImageEnhance.Color(rgb).enhance(1.04)
        out_rgba = rgb.convert("RGBA")
        out_rgba.putalpha(rgba.getchannel("A"))
        return out_rgba

    def place(i, rgba, target):
        y0, y1, x0, x1 = cell_box(i)
        cell_h, cell_w = y1 - y0, x1 - x0
        th = min(int(round(cell_h * target)), cell_h - 8)
        sw, sh = rgba.size
        scale = th / max(sh, 1)
        mw = int(cell_w * max_w_frac[i])
        if sw * scale > mw:
            # Prefer hitting height for L5+; allow a bit more width.
            if i >= 4:
                mw = min(cell_w - 8, max(mw, int(cell_w * 0.92)))
            if sw * scale > mw:
                # For wide horizontal pan flute, stretch height after width clamp.
                scale_w = mw / max(sw, 1)
                nw = max(1, int(sw * scale_w))
                nh = th if i >= 4 else max(1, int(sh * scale_w))
                resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
            else:
                nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
                resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        else:
            nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
            resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        # Guarantee late tiers hit target height.
        if i >= 4 and resized.size[1] < int(cell_h * target * 0.97):
            nh = min(cell_h - 8, th)
            nw = min(cell_w - 8, max(resized.size[0], int(nh * resized.size[0] / max(resized.size[1], 1))))
            resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        px = x0 + (cell_w - resized.size[0]) // 2
        py = y0 + (cell_h - resized.size[1]) // 2
        out.paste(resized, (px, py), resized)
        log.append(f"L{i+1} {resized.size[0]}x{resized.size[1]} target={target}")

    for i, t in enumerate(targets):
        y0, y1, x0, x1 = cell_box(i)
        rgba = extract(src_pick[i][y0:y1, x0:x1], strip_side_rails=(i == 6))
        if rgba is None:
            log.append(f"FAIL L{i+1}")
            continue
        if i == 3:
            rgba = boost_l4_keys(rgba)
        place(i, rgba, t)

    path = ROOT / "sheet_r15.jpg"
    out.save(path, quality=95)
    out.save(ROOT / "volume_layout_r15.jpg", quality=95)
    arr2 = np.array(out)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    (ROOT / "height_r15_composite.log").write_text(
        "\n".join(log)
        + "\nheights "
        + str([round(x, 3) for x in hs])
        + "\n"
        + ("PASS" if ok else "FAIL")
        + "\n"
        + "\n".join(iss),
        encoding="utf-8",
    )
    print("ok", ok)
    print("heights", [round(x, 3) for x in hs])
    print("\n".join(iss) if iss else "no issues")
except Exception:
    ERR.write_text(traceback.format_exc(), encoding="utf-8")
    raise
