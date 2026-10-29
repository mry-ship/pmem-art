"""Put each merge item fully on one equal square.

Equal 1/8 columns slice wide items (printer, cake) and, on the kitchen
sheet, there are nine objects so an eight-way cut always hits one.
Components are taken from the object core, then each box is padded only
up to the gap before the next object.
"""
from pathlib import Path

import numpy as np
from PIL import Image

BASE = Path(__file__).resolve().parent / "images"

# Core threshold. Faint grid lines and soft shadows stay below this.
CORE = {
    "merge_a": 34,
    "merge_b": 48,
    "merge_c": 52,
}

# Fixed vertical cuts on the 1280px contact sheet (faint grid), not equal blobs.
SHEET_X: dict[str, list[int]] = {
    "merge_b": [i * 1280 // 8 for i in range(9)],
    "merge_c": [0, 145, 290, 432, 573, 728, 880, 1029, 1280],
}


def densest_band(mask: np.ndarray) -> tuple[int, int]:
    h, w = mask.shape
    row_sum = mask.sum(axis=1).astype(np.float32)
    row_std = mask.astype(np.float32).std(axis=1)
    score = row_sum * (row_std + 0.05)
    if score.max() <= 0:
        return int(h * 0.25), int(h * 0.75)
    peak = int(np.argmax(score))
    thr = max(score.max() * 0.22, 1.0)
    lo = peak
    while lo > 0 and score[lo - 1] >= thr * 0.4:
        lo -= 1
    hi = peak
    while hi < h - 1 and score[hi + 1] >= thr * 0.4:
        hi += 1
    span = max(hi - lo + 1, int(h * 0.2))
    win = int(np.clip(span * 1.15, h * 0.24, h * 0.42))
    y0 = int(np.clip(peak - win // 2, 0, h - win))
    return y0, y0 + win


def grid_column_spans(dist: np.ndarray, thr: float, cuts: list[int]) -> list[tuple[int, int, int, int]]:
    h = dist.shape[0]
    soft = thr * 0.92
    spans: list[tuple[int, int, int, int]] = []
    for i in range(len(cuts) - 1):
        x0, x1 = cuts[i], cuts[i + 1]
        col_w = max(1, x1 - x0)
        sl = dist[:, x0:x1] > thr * 1.12
        row_need = max(14, int(col_w * 0.09))
        margin = min(48, h // 8)
        interior = sl[margin : h - margin]
        rows_rel = np.where(interior.sum(axis=1) > row_need)[0]
        if len(rows_rel) == 0:
            y0, y1 = densest_band(sl)
        else:
            rows = rows_rel + margin
            y0 = max(0, int(rows[0]) - 18)
            y1 = min(h, int(rows[-1]) + 22)
        spans.append((x0, y0, x1, y1))
    return spans


def sheet_bg(arr: np.ndarray) -> np.ndarray:
    ring = np.concatenate(
        [
            arr[:8].reshape(-1, 3),
            arr[-8:].reshape(-1, 3),
            arr[:, :8].reshape(-1, 3),
            arr[:, -8:].reshape(-1, 3),
        ]
    )
    return np.median(ring, axis=0)


def label_components(mask: np.ndarray) -> list[tuple[int, int, int, int, int]]:
    """Return (area, x0, y0, x1, y1) for each 4-connected blob. x1/y1 exclusive."""
    h, w = mask.shape
    seen = np.zeros(mask.shape, dtype=bool)
    boxes: list[tuple[int, int, int, int, int]] = []
    ys, xs = np.where(mask)
    for y, x in zip(ys.tolist(), xs.tolist()):
        if seen[y, x]:
            continue
        stack = [(y, x)]
        seen[y, x] = True
        area = 0
        x0 = x1 = x
        y0 = y1 = y
        while stack:
            cy, cx = stack.pop()
            area += 1
            x0 = min(x0, cx)
            x1 = max(x1, cx)
            y0 = min(y0, cy)
            y1 = max(y1, cy)
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    stack.append((ny, nx))
        boxes.append((area, x0, y0, x1 + 1, y1 + 1))
    return boxes


def object_boxes(dist: np.ndarray, thr: float) -> list[tuple[int, int, int, int]]:
    mask = dist > thr
    boxes = [b for b in label_components(mask) if b[0] > 180]
    boxes.sort(key=lambda b: b[1])
    merged: list[list[int]] = []
    for area, x0, y0, x1, y1 in boxes:
        if not merged:
            merged.append([x0, y0, x1, y1])
            continue
        px0, py0, px1, py1 = merged[-1]
        overlap = min(px1, x1) - max(px0, x0)
        narrow = min(px1 - px0, x1 - x0)
        if overlap > narrow * 0.35:
            merged[-1] = [min(px0, x0), min(py0, y0), max(px1, x1), max(py1, y1)]
        else:
            merged.append([x0, y0, x1, y1])
    boxes = [tuple(b) for b in merged]
    widths = sorted(b[2] - b[0] for b in boxes)
    median = widths[len(widths) // 2] if widths else 160
    # A shadow can glue two neighbors into one wide box. Split that box at
    # the thinnest core column, and only when it is clearly wider than one item.
    split: list[tuple[int, int, int, int]] = []
    for x0, y0, x1, y1 in boxes:
        if (x1 - x0) > median * 1.65 and (x1 - x0) > 200:
            col = dist_band(dist, y0, y1, thr)[x0:x1]
            margin = max(24, (x1 - x0) // 5)
            interior = col[margin:-margin]
            # Only cut when the interior actually goes empty. A wide single
            # object (bread maker) stays one square.
            if len(interior) and float(interior.min()) < max(float(col.max()) * 0.18, 3):
                cut = x0 + margin + int(np.argmin(interior))
                split.append((x0, y0, cut, y1))
                split.append((cut, y0, x1, y1))
                continue
        split.append((x0, y0, x1, y1))
    return split


def dist_band(dist: np.ndarray, y0: int, y1: int, thr: float) -> np.ndarray:
    return (dist[y0:y1] > thr).sum(axis=0)


def projection_boxes(dist: np.ndarray, thr: float) -> list[tuple[int, int, int, int]]:
    """Fallback when a faint grid glues every cell into one component."""
    col = (dist > thr).sum(axis=0)
    on = col > 8
    spans: list[tuple[int, int]] = []
    start = None
    for x, flag in enumerate(on.tolist()):
        if flag and start is None:
            start = x
        elif not flag and start is not None:
            if x - start > 24:
                spans.append((start, x))
            start = None
    if start is not None and dist.shape[1] - start > 24:
        spans.append((start, dist.shape[1]))
    boxes = []
    h = dist.shape[0]
    for x0, x1 in spans:
        rows = np.where((dist[:, x0:x1] > thr).any(axis=1))[0]
        if len(rows) == 0:
            continue
        # Drop full-height grid: keep the densest vertical run.
        hits = (dist[:, x0:x1] > thr).sum(axis=1).astype(np.float32)
        smooth = np.convolve(hits, np.ones(15) / 15, mode="same")
        peak = int(np.argmax(smooth))
        level = max(float(smooth[peak]) * 0.35, 3.0)
        lo = hi = peak
        while lo > 0 and smooth[lo - 1] >= level:
            lo -= 1
        while hi < h - 1 and smooth[hi + 1] >= level:
            hi += 1
        boxes.append((x0, lo, x1, hi + 1))
    return boxes


def boxes_in_columns(dist: np.ndarray, thr: float, spans: list[tuple[int, int, int, int]]) -> list[tuple[int, int, int, int]]:
    """One object per column span; crop stays inside the span (no grid-line bleed)."""
    hard = thr * 1.18
    out: list[tuple[int, int, int, int]] = []
    for x0, y0, x1, y1 in spans:
        sl = dist[y0:y1, x0:x1] > hard
        rows = np.where(sl.sum(axis=1) > 3)[0]
        cols = np.where(sl.sum(axis=0) > 2)[0]
        if len(rows) == 0 or len(cols) == 0:
            out.append((x0, y0, x1, y1))
            continue
        ox0 = x0 + int(cols[0])
        ox1 = x0 + int(cols[-1]) + 1
        oy0 = y0 + int(rows[0])
        oy1 = y0 + int(rows[-1]) + 1
        out.append((ox0, oy0, ox1, oy1))
    return out


def place(name: str, side: int = 1024) -> None:
    src = BASE / name / "sheet.jpg"
    im = Image.open(src).convert("RGB")
    arr = np.asarray(im)
    bg = sheet_bg(arr.astype(np.float32))
    dist = np.linalg.norm(arr.astype(np.float32) - bg, axis=2)
    color = tuple(int(round(c)) for c in bg)
    h, w = arr.shape[:2]
    col_spans: list[tuple[int, int, int, int]] = []
    if name in SHEET_X:
        col_spans = grid_column_spans(dist, CORE[name], SHEET_X[name])
    if name == "merge_a":
        boxes = object_boxes(dist, CORE[name])
        tight: list[tuple[int, int, int, int]] = []
        for x0, y0, x1, y1 in boxes:
            sl = dist[y0:y1, x0:x1] > CORE[name] * 1.18
            rows = np.where(sl.sum(axis=1) > 3)[0]
            cols = np.where(sl.sum(axis=0) > 2)[0]
            if len(rows) == 0 or len(cols) == 0:
                tight.append((x0, y0, x1, y1))
                continue
            tight.append((x0 + int(cols[0]), y0 + int(rows[0]), x0 + int(cols[-1]) + 1, y0 + int(rows[-1]) + 1))
        boxes = tight
        col_spans = []
    elif not col_spans:
        proj = projection_boxes(dist, CORE[name])
        if len(proj) >= 8:
            col_spans = proj[:8]
            boxes = boxes_in_columns(dist, CORE[name], col_spans)
        else:
            boxes = object_boxes(dist, CORE[name])
            tight = []
            for x0, y0, x1, y1 in boxes:
                sl = dist[y0:y1, x0:x1] > CORE[name] * 1.18
                rows = np.where(sl.sum(axis=1) > 3)[0]
                cols = np.where(sl.sum(axis=0) > 2)[0]
                if len(rows) == 0 or len(cols) == 0:
                    tight.append((x0, y0, x1, y1))
                    continue
                tight.append(
                    (x0 + int(cols[0]), y0 + int(rows[0]), x0 + int(cols[-1]) + 1, y0 + int(rows[-1]) + 1)
                )
            boxes = tight
            col_spans = []
    if name == "merge_a" and len(boxes) == 9:
        # The sheet drew an extra rolling pin between the blender and the bread maker.
        # The ladder is eight items; that pin is not a tier.
        boxes = boxes[:7] + boxes[8:]
    outdir = BASE / name
    # Drop stale extra tiles from a previous wrong count.
    for old in outdir.glob("L*.jpg"):
        old.unlink()
    if name in SHEET_X and col_spans:
        for i, (sx0, sy0, sx1, sy1) in enumerate(col_spans):
            cx0, cx1 = sx0 + 4, sx1 - 4
            cy0 = max(0, sy0 - 6)
            cy1 = min(h, sy1 + 6)
            crop = im.crop((cx0, cy0, cx1, cy1))
            canvas = Image.new("RGB", (side, side), color)
            cw, ch = crop.size
            fit = int(side * 0.68)
            scale = min(fit / cw, fit / ch)
            nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
            crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
            canvas.paste(crop, ((side - nw) // 2, (side - nh) // 2))
            dest = outdir / f"L{i + 1:02d}.jpg"
            canvas.save(dest, quality=93)
            print(f"{dest.name} cell x[{cx0}:{cx1}] y[{cy0}:{cy1}]")
        print(f"{name}: {len(col_spans)} squares")
        return

    span_x = col_spans[: len(boxes)] if len(col_spans) >= len(boxes) else None
    for i, (x0, y0, x1, y1) in enumerate(boxes):
        bw, bh = x1 - x0, y1 - y0
        pad_x = int(max(12, min(bw * 0.14, 32)))
        pad_y = int(max(16, min(bh * 0.28, 56)))
        if span_x and i < len(span_x):
            sx0, sy0, sx1, sy1 = span_x[i]
            # Full cell: one column wide, object band tall (not a tight bbox).
            cx0, cx1 = sx0 + 4, sx1 - 4
            cy0 = max(0, sy0 - 6)
            cy1 = min(h, sy1 + 6)
            crop = im.crop((cx0, cy0, cx1, cy1))
            canvas = Image.new("RGB", (side, side), color)
            cw, ch = crop.size
            fit = int(side * 0.68)
            scale = min(fit / cw, fit / ch)
            nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
            crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
            canvas.paste(crop, ((side - nw) // 2, (side - nh) // 2))
            dest = outdir / f"L{i + 1:02d}.jpg"
            canvas.save(dest, quality=93)
            print(f"{dest.name} cell x[{cx0}:{cx1}] y[{cy0}:{cy1}]")
            continue
        else:
            prev_r = boxes[i - 1][2] if i else 0
            next_l = boxes[i + 1][0] if i + 1 < len(boxes) else w
            left_lim = 0 if i == 0 else (prev_r + x0) // 2 + 2
            right_lim = w if i + 1 >= len(boxes) else (x1 + next_l) // 2 - 2
            cx0 = max(left_lim, x0 - pad_x)
            cx1 = min(right_lim, x1 + pad_x)
        cy0 = max(0, y0 - pad_y)
        cy1 = min(h, y1 + pad_y)
        crop = im.crop((cx0, cy0, cx1, cy1))
        canvas = Image.new("RGB", (side, side), color)
        cw, ch = crop.size
        fit = int(side * 0.68)
        scale = min(fit / cw, fit / ch)
        nw, nh = max(1, int(cw * scale)), max(1, int(ch * scale))
        crop = crop.resize((nw, nh), Image.Resampling.LANCZOS)
        canvas.paste(crop, ((side - nw) // 2, (side - nh) // 2))
        dest = outdir / f"L{i + 1:02d}.jpg"
        canvas.save(dest, quality=93)
        print(f"{dest.name} box x[{x0}:{x1}] y[{y0}:{y1}]")
    print(f"{name}: {len(boxes)} squares")


def main() -> None:
    for name in ("merge_a", "merge_b", "merge_c"):
        print("==", name)
        place(name)


if __name__ == "__main__":
    main()
