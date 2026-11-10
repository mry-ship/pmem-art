from pathlib import Path
from PIL import Image
import numpy as np
from skills_kit.merge_relation import (
    _cell_subject_height_ratio,
    audit_overview_sheet,
    _border_median,
)

src = Image.open("assets/skill_20261110_gh_portrait_v2/merge_jam/sheet_r9.jpg").convert("RGB")
alt = Image.open("assets/skill_20261110_gh_portrait_v2/merge_jam/sheet_r7.jpg").convert("RGB")
W, H = src.size
rows, cols = 4, 2
targets = [0.42, 0.50, 0.58, 0.66, 0.74, 0.80, 0.88, 0.96]
arr = np.array(src)
arr_alt = np.array(alt)
out = Image.new("RGB", (W, H), (0, 0, 0))
log = []


def extract_subject(cell_arr):
    h, w = cell_arr.shape[:2]
    bg = _border_median(cell_arr, band=max(1, min(4, h // 10, w // 10)))
    diff = np.linalg.norm(cell_arr.astype(np.float32) - bg, axis=2)
    content = diff > 28
    if not content.any():
        return None
    ys, xs = np.where(content)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    pad = 2
    y0 = max(0, y0 - pad)
    x0 = max(0, x0 - pad)
    y1 = min(h, y1 + pad)
    x1 = min(w, x1 + pad)
    ca = cell_arr[y0:y1, x0:x1]
    d = np.linalg.norm(ca.astype(np.float32) - bg, axis=2)
    mask = (d > 28).astype(np.uint8) * 255
    rgba = Image.fromarray(ca).convert("RGBA")
    rgba.putalpha(Image.fromarray(mask))
    return rgba


for i, t in enumerate(targets):
    r, c = divmod(i, cols)
    y0, y1 = (H * r) // rows, (H * (r + 1)) // rows
    x0, x1 = (W * c) // cols, (W * (c + 1)) // cols
    base = arr_alt if i >= 6 else arr
    cell = base[y0:y1, x0:x1]
    sub = extract_subject(cell)
    if sub is None:
        log.append(f"fail extract L{i+1}")
        continue
    cell_h = y1 - y0
    cell_w = x1 - x0
    th = int(cell_h * t)
    sw, sh = sub.size
    max_w_frac = [0.50, 0.62, 0.66, 0.42, 0.48, 0.58, 0.86, 0.96][i]
    max_w = int(cell_w * max_w_frac)
    scale = th / max(sh, 1)
    if sw * scale > max_w and i < 6:
        scale = max_w / max(sw, 1)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    # Prefer hitting target height for L7/L8 even if wider
    if i >= 6 and nh < th:
        scale = th / max(sh, 1)
        nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
        if nw > cell_w - 8:
            scale = (cell_w - 8) / max(sw, 1)
            nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    # If still below target height (wide flat tart), stretch height a bit
    if nh < int(cell_h * t * 0.97) and i >= 6:
        need = int(cell_h * t)
        nw2 = min(cell_w - 8, max(nw, int(nw * 1.05)))
        nh2 = need
        resized = sub.resize((nw2, nh2), Image.Resampling.LANCZOS)
        nw, nh = nw2, nh2
    else:
        resized = sub.resize((nw, nh), Image.Resampling.LANCZOS)
    px = x0 + (cell_w - nw) // 2
    py = y0 + (cell_h - nh) // 2
    px = min(max(x0 + 2, px), x1 - nw - 2)
    py = min(max(y0 + 2, py), y1 - nh - 2)
    out.paste(resized, (px, py), resized)
    log.append(f"L{i+1} placed {nw}x{nh} target_h={th}")

path = Path("assets/skill_20261110_gh_portrait_v2/merge_jam/volume_layout_r10.jpg")
out.save(path, quality=95)
arr2 = np.array(out)
hs = []
for r in range(4):
    y0, y1 = (H * r) // 4, (H * (r + 1)) // 4
    for c in range(2):
        x0, x1 = (W * c) // 2, (W * (c + 1)) // 2
        hs.append(_cell_subject_height_ratio(arr2[y0:y1, x0:x1]))
ok, iss = audit_overview_sheet(path, rows=4, cols=2)
Path("assets/skill_20261110_gh_portrait_v2/merge_jam/volume_layout_r10.log").write_text(
    "\n".join(log)
    + "\nheights "
    + str([round(x, 3) for x in hs])
    + "\n"
    + ("PASS" if ok else "FAIL")
    + "\n"
    + "\n".join(iss),
    encoding="utf-8",
)
print("done")
