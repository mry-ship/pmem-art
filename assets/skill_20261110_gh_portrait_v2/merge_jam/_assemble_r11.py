"""Assemble overview from best cells with exact target heights."""
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parents[2]
sys.path.insert(0, str(PROJ))
ASSETS_CURSOR = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")
ERR = ROOT / "_assemble_err.txt"

try:
    from PIL import Image, ImageFilter
    import numpy as np
    from skills_kit.merge_relation import (
        _cell_subject_height_ratio,
        audit_overview_sheet,
        _border_median,
    )

    W, H = 720, 1280
    rows, cols = 4, 2
    targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.96]
    max_w = [0.48, 0.58, 0.62, 0.40, 0.46, 0.56, 0.86, 0.96]
    out = Image.new("RGB", (W, H), (0, 0, 0))
    log = []

    def extract_from_sheet(sheet_path, idx):
        im = np.array(Image.open(sheet_path).convert("RGB"))
        h, w = im.shape[:2]
        r, c = divmod(idx, cols)
        y0, y1 = (h * r) // rows, (h * (r + 1)) // rows
        x0, x1 = (w * c) // cols, (w * (c + 1)) // cols
        return extract_rgba(im[y0:y1, x0:x1])

    def extract_rgba(cell_arr):
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

    def extract_file(path):
        arr = np.array(Image.open(path).convert("RGB"))
        return extract_rgba(arr)

    # Sources
    sheet_r9 = ROOT / "sheet_r9.jpg"
    sheet_r7 = ROOT / "sheet_r7.jpg"
    cells = {
        0: extract_from_sheet(sheet_r9, 0),
        1: extract_from_sheet(sheet_r9, 1),
        2: extract_from_sheet(sheet_r9, 2),
        3: extract_file(ASSETS_CURSOR / "cell_l4_juice.jpg"),
        4: extract_file(ASSETS_CURSOR / "cell_l5_smoothie.jpg"),
        5: extract_file(ASSETS_CURSOR / "cell_l6_jar.jpg"),
        6: extract_file(ASSETS_CURSOR / "cell_l7_tall_tart.jpg"),
        7: extract_file(ASSETS_CURSOR / "cell_l8_feast.jpg"),
    }
    # fallbacks
    if cells[3] is None:
        cells[3] = extract_from_sheet(ROOT / "sheet_r5.jpg", 3)
    if cells[5] is None:
        cells[5] = extract_from_sheet(ROOT / "sheet_r5.jpg", 5)
    if cells[4] is None:
        cells[4] = extract_from_sheet(sheet_r7, 4)
    if cells[6] is None:
        cells[6] = extract_from_sheet(sheet_r7, 6)
    if cells[7] is None:
        cells[7] = extract_from_sheet(sheet_r7, 7)

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
        # Prefer hitting height for high tiers
        if nh < int(cell_h * t * 0.97):
            nh = min(cell_h - 8, int(cell_h * t))
            nw = min(cell_w - 8, max(int(sw * (nh / max(sh, 1))), int(mw * 0.9)))
        resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        px = x0 + (cell_w - nw) // 2
        py = y0 + (cell_h - nh) // 2
        out.paste(resized, (px, py), resized)
        log.append(f"L{i+1} {nw}x{nh} th={th}")

    path = ROOT / "sheet_r11.jpg"
    out.save(path, quality=95)
    arr2 = np.array(out)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    (ROOT / "height_r11.log").write_text(
        "\n".join(log)
        + "\nheights "
        + str([round(x, 3) for x in hs])
        + "\n"
        + ("PASS" if ok else "FAIL")
        + "\n"
        + "\n".join(iss),
        encoding="utf-8",
    )
    # also copy cells into merge folder
    for name in (
        "cell_l4_juice.jpg",
        "cell_l5_smoothie.jpg",
        "cell_l6_jar.jpg",
        "cell_l7_tall_tart.jpg",
        "cell_l8_feast.jpg",
    ):
        src = ASSETS_CURSOR / name
        if src.exists():
            Image.open(src).convert("RGB").save(ROOT / name, quality=92)
except Exception:
    ERR.write_text(traceback.format_exc(), encoding="utf-8")
    raise
