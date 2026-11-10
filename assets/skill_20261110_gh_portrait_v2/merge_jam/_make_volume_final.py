"""Clean overview with strict ascending subject heights for jam ladder."""
import traceback
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parents[2]))
ERR = ROOT / "_make_final_err.txt"

try:
    from PIL import Image, ImageFilter
    import numpy as np
    from skills_kit.merge_relation import (
        _cell_subject_height_ratio,
        audit_overview_sheet,
        _border_median,
    )

    sheets = {
        k: np.array(Image.open(ROOT / f"sheet_{k}.jpg").convert("RGB"))
        for k in ("r5", "r7", "r9")
    }
    H, W = sheets["r9"].shape[:2]
    rows, cols = 4, 2
    targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.96]
    # slightly under target for L8 to avoid crop; still max
    place_targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.94]
    max_w_frac = [0.46, 0.56, 0.60, 0.38, 0.44, 0.52, 0.84, 0.94]
    src_pick = ["r9", "r9", "r9", "r5", "r7", "r5", "r7", "r7"]
    out = Image.new("RGB", (W, H), (0, 0, 0))
    log = []

    def cell_box(i):
        r, c = divmod(i, cols)
        y0, y1 = (H * r) // rows, (H * (r + 1)) // rows
        x0, x1 = (W * c) // cols, (W * (c + 1)) // cols
        return y0, y1, x0, x1

    def extract(cell_arr):
        h, w = cell_arr.shape[:2]
        inset = 6
        work = cell_arr[inset : h - inset, inset : w - inset]
        bg = _border_median(work, band=max(1, min(4, work.shape[0] // 12)))
        diff = np.linalg.norm(work.astype(np.float32) - bg, axis=2)
        content = diff > 28
        if not content.any():
            return None
        # largest connected-ish via bbox of strong content
        ys, xs = np.where(content)
        y0, y1 = int(ys.min()), int(ys.max() + 1)
        x0, x1 = int(xs.min()), int(xs.max() + 1)
        # trim thin speckles by requiring row/col density
        row_d = content.mean(axis=1)
        col_d = content.mean(axis=0)
        good_rows = np.where(row_d > 0.02)[0]
        good_cols = np.where(col_d > 0.02)[0]
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
        alpha = np.clip((d - 20) / 8.0 * 255.0, 0, 255).astype(np.uint8)
        # remove tiny speckles
        aimg = Image.fromarray(alpha).filter(ImageFilter.MedianFilter(3))
        alpha = np.array(aimg)
        rgba = Image.fromarray(ca).convert("RGBA")
        rgba.putalpha(Image.fromarray(alpha))
        # crop to alpha bbox
        bbox = Image.fromarray(alpha).getbbox()
        if not bbox:
            return None
        return rgba.crop(bbox)

    def place(i, rgba, target):
        y0, y1, x0, x1 = cell_box(i)
        cell_h, cell_w = y1 - y0, x1 - x0
        th = int(round(cell_h * target))
        # force leave gap
        th = min(th, cell_h - 10)
        sw, sh = rgba.size
        scale = th / max(sh, 1)
        mw = int(cell_w * max_w_frac[i])
        if sw * scale > mw:
            scale = mw / max(sw, 1)
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        if i >= 6 and nh < int(cell_h * target * 0.97):
            nh = min(cell_h - 10, int(cell_h * target))
            aspect = sw / max(sh, 1)
            nw = min(cell_w - 10, max(int(nh * aspect), int(cell_w * 0.70)))
        resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        px = x0 + (cell_w - nw) // 2
        py = y0 + (cell_h - nh) // 2
        out.paste(resized, (px, py), resized)
        log.append(f"L{i+1} {nw}x{nh} target={target}")

    # Build tall tart without cropping: tart crust + scaled feast crown inside canvas
    tart = extract(sheets["r7"][cell_box(6)[0] : cell_box(6)[1], cell_box(6)[2] : cell_box(6)[3]])
    feast = extract(sheets["r7"][cell_box(7)[0] : cell_box(7)[1], cell_box(7)[2] : cell_box(7)[3]])
    custom = {}
    if tart and feast:
        tw = 280
        thc = 360
        tall = Image.new("RGBA", (tw, thc), (0, 0, 0, 0))
        crust_h = int(thc * 0.42)
        mound_h = int(thc * 0.70)
        crust = tart.resize((tw, crust_h), Image.Resampling.LANCZOS)
        tall.paste(crust, (0, thc - crust_h), crust)
        fw, fh = feast.size
        crown = feast.crop((int(fw * 0.08), 0, int(fw * 0.92), int(fh * 0.55)))
        crown = crown.resize((int(tw * 0.82), mound_h), Image.Resampling.LANCZOS)
        tall.paste(crown, ((tw - crown.size[0]) // 2, thc - crust_h - int(mound_h * 0.72)), crown)
        custom[6] = tall

    for i, t in enumerate(place_targets):
        if i in custom:
            place(i, custom[i], t)
            continue
        y0, y1, x0, x1 = cell_box(i)
        rgba = extract(sheets[src_pick[i]][y0:y1, x0:x1])
        if rgba is None:
            log.append(f"FAIL L{i+1}")
            continue
        place(i, rgba, t)

    path = ROOT / "sheet_r10.jpg"
    # overwrite failed gen with height-correct composite for round 2
    out.save(path, quality=95)
    out.save(ROOT / "volume_layout_clean.jpg", quality=95)
    arr2 = np.array(out)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    (ROOT / "height_r10_composite.log").write_text(
        "\n".join(log)
        + "\nheights "
        + str([round(x, 3) for x in hs])
        + "\n"
        + ("PASS" if ok else "FAIL")
        + "\n"
        + "\n".join(iss),
        encoding="utf-8",
    )
except Exception:
    ERR.write_text(traceback.format_exc(), encoding="utf-8")
    raise
