"""Assemble sheet_r16 with forced height ladder; keep appetizing L5/L8."""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parents[2]
sys.path.insert(0, str(PROJ))
ASSETS_CURSOR = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets"
)
ERR = ROOT / "_assemble_r16_err.txt"

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
    max_w = [0.48, 0.58, 0.62, 0.38, 0.46, 0.56, 0.86, 0.94]
    out = Image.new("RGB", (W, H), (0, 0, 0))
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

    sheet_r13 = ROOT / "sheet_r13.jpg"
    sheet_r14 = ROOT / "sheet_r14.jpg"
    cells = {
        0: extract_from_sheet(sheet_r13, 0),
        1: extract_from_sheet(sheet_r13, 1),
        2: extract_from_sheet(sheet_r13, 2),
        3: extract_from_sheet(sheet_r13, 3),
        4: extract_from_sheet(sheet_r13, 4),  # appetizing smoothie
        5: extract_from_sheet(sheet_r13, 5),
        6: extract_file(ASSETS_CURSOR / "cell_l7_tall_tart_r7.jpg")
        or extract_from_sheet(sheet_r14, 6),
        7: extract_file(ASSETS_CURSOR / "cell_l8_cake_r7.jpg")
        or extract_from_sheet(sheet_r13, 7),
    }
    for i in range(8):
        if cells[i] is None:
            cells[i] = extract_from_sheet(sheet_r14, i)
            log.append(f"fallback L{i+1} from r14")

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
        log.append(f"L{i+1} {nw}x{nh} th={th}")

    path = ROOT / "sheet_r16.jpg"
    out.save(path, quality=95)
    # also copy to cursor assets for visibility
    out.save(ASSETS_CURSOR / "sheet_r16.jpg", quality=95)

    arr2 = np.array(out)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    (ROOT / "height_r16.log").write_text(
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
    print("\n".join(iss))
except Exception:
    ERR.write_text(traceback.format_exc(), encoding="utf-8")
    raise
