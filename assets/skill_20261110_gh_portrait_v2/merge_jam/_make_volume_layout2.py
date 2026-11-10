"""Rebuild overview with exact target heights from best prior SKU cells."""
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
ERR = Path(__file__).with_name("_make2_err.txt")
try:
    from PIL import Image
    import numpy as np
    from skills_kit.merge_relation import (
        _cell_subject_height_ratio,
        audit_overview_sheet,
        _border_median,
    )
except Exception:
    ERR.write_text(traceback.format_exc(), encoding="utf-8")
    raise

try:
    ROOT = Path(__file__).resolve().parent
    sheets = {
        "r5": np.array(Image.open(ROOT / "sheet_r5.jpg").convert("RGB")),
        "r7": np.array(Image.open(ROOT / "sheet_r7.jpg").convert("RGB")),
        "r9": np.array(Image.open(ROOT / "sheet_r9.jpg").convert("RGB")),
    }
    # Prefer sources with less clipping per cell
    src_pick = ["r9", "r9", "r9", "r5", "r7", "r5", "r7", "r7"]
    targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.96]
    max_w_frac = [0.48, 0.58, 0.62, 0.40, 0.46, 0.55, 0.90, 0.96]
    H, W = sheets["r9"].shape[:2]
    rows, cols = 4, 2
    out = Image.new("RGB", (W, H), (0, 0, 0))
    log = []

    def cell_slice(arr, i):
        r, c = divmod(i, cols)
        y0, y1 = (H * r) // rows, (H * (r + 1)) // rows
        x0, x1 = (W * c) // cols, (W * (c + 1)) // cols
        return arr[y0:y1, x0:x1], (x0, y0, x1, y1)

    def extract_rgba(cell_arr, soft=6):
        h, w = cell_arr.shape[:2]
        inset = 4
        work = cell_arr[inset : h - inset, inset : w - inset]
        bg = _border_median(work, band=max(1, min(4, work.shape[0] // 12)))
        diff = np.linalg.norm(work.astype(np.float32) - bg, axis=2)
        content = diff > 26
        if not content.any():
            return None
        ys, xs = np.where(content)
        y0, y1 = ys.min(), ys.max() + 1
        x0, x1 = xs.min(), xs.max() + 1
        pad = 3
        y0 = max(0, y0 - pad)
        x0 = max(0, x0 - pad)
        y1 = min(work.shape[0], y1 + pad)
        x1 = min(work.shape[1], x1 + pad)
        ca = work[y0:y1, x0:x1]
        d = np.linalg.norm(ca.astype(np.float32) - bg, axis=2)
        alpha = np.clip((d - 18) / soft * 255.0, 0, 255).astype(np.uint8)
        rgba = Image.fromarray(ca).convert("RGBA")
        rgba.putalpha(Image.fromarray(alpha))
        return rgba

    def place(i, rgba, target):
        r, c = divmod(i, cols)
        y0, y1 = (H * r) // rows, (H * (r + 1)) // rows
        x0, x1 = (W * c) // cols, (W * (c + 1)) // cols
        cell_h, cell_w = y1 - y0, x1 - x0
        th = int(round(cell_h * target))
        sw, sh = rgba.size
        scale = th / max(sh, 1)
        mw = int(cell_w * max_w_frac[i])
        if sw * scale > mw:
            scale = mw / max(sw, 1)
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        if i >= 6 and nh < int(cell_h * target * 0.98):
            nh = int(cell_h * target)
            nw = min(cell_w - 10, max(int(sw * (nh / max(sh, 1))), int(cell_w * 0.72)))
        resized = rgba.resize((nw, nh), Image.Resampling.LANCZOS)
        px = x0 + (cell_w - nw) // 2
        py = y0 + (cell_h - nh) // 2
        px = min(max(x0 + 3, px), x1 - nw - 3)
        py = min(max(y0 + 3, py), y1 - nh - 3)
        out.paste(resized, (px, py), resized)
        log.append(f"L{i+1} {nw}x{nh} th={th}")

    tart_cell, _ = cell_slice(sheets["r7"], 6)
    feast_cell, _ = cell_slice(sheets["r7"], 7)
    tart = extract_rgba(tart_cell)
    feast = extract_rgba(feast_cell)
    if tart and feast:
        tw = max(tart.size[0], int(tart.size[0] * 1.15))
        th_canvas = int(tart.size[1] * 1.85)
        tall = Image.new("RGBA", (tw, th_canvas), (0, 0, 0, 0))
        tb = tart.resize((tw, int(tart.size[1] * 1.05)), Image.Resampling.LANCZOS)
        tall.paste(tb, ((tw - tb.size[0]) // 2, th_canvas - tb.size[1]), tb)
        fw, fh = feast.size
        crown = feast.crop((0, 0, fw, int(fh * 0.62))).resize(
            (int(tw * 0.86), int(th_canvas * 0.62)), Image.Resampling.LANCZOS
        )
        tall.paste(crown, ((tw - crown.size[0]) // 2, int(th_canvas * 0.05)), crown)
        custom = {6: tall}
    else:
        custom = {}

    for i, t in enumerate(targets):
        if i in custom:
            place(i, custom[i], t)
            continue
        cell, _ = cell_slice(sheets[src_pick[i]], i)
        rgba = extract_rgba(cell)
        if rgba is None:
            log.append(f"FAIL L{i+1}")
            continue
        place(i, rgba, t)

    path = ROOT / "volume_layout_r10b.jpg"
    out.save(path, quality=95)
    arr2 = np.array(out)
    hs = []
    for r in range(4):
        y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
        for c in range(2):
            x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
            hs.append(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]))
    ok, iss = audit_overview_sheet(path, rows=4, cols=2)
    (ROOT / "volume_layout_r10b.log").write_text(
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
