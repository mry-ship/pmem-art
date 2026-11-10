# -*- coding: utf-8 -*-
"""Sample real HEX from the fairy-garden style plate. Read-only."""
import colorsys
from collections import Counter
from pathlib import Path

from PIL import Image

src = Path(r"assets/skill_20261109/_refs/ref_style_fairy_garden.png")
im = Image.open(src).convert("RGB")
w, h = im.size
small = im.resize((80, 80), Image.Resampling.BOX)
q = small.quantize(colors=16, method=Image.Quantize.MEDIANCUT).convert("RGB")
counts = Counter(q.getdata())
total = sum(counts.values())

def hex_of(rgb):
    return "#{:02X}{:02X}{:02X}".format(*rgb)

def hsv_of(rgb):
    r, g, b = [c / 255 for c in rgb]
    return colorsys.rgb_to_hsv(r, g, b)

lines = [f"size={w}x{h}", "QUANTIZED"]
for rgb, n in counts.most_common():
    hh, ss, vv = hsv_of(rgb)
    lines.append(f"{hex_of(rgb)} n={n:5d} pct={100*n/total:5.1f} h={hh*360:6.1f} s={ss:4.2f} v={vv:4.2f}")

# Region medians: name, box as fractions (l,t,r,b)
regions = {
    "grass_center": (0.42, 0.62, 0.62, 0.82),
    "leaf_left": (0.02, 0.28, 0.16, 0.55),
    "leaf_right": (0.84, 0.22, 0.98, 0.48),
    "sky_gap": (0.30, 0.02, 0.48, 0.12),
    "wood_roof_left": (0.22, 0.48, 0.38, 0.58),
    "door_brown": (0.30, 0.55, 0.40, 0.68),
    "wall_cream": (0.24, 0.50, 0.34, 0.58),
    "purple_cap": (0.28, 0.38, 0.40, 0.50),
    "tower_purple": (0.55, 0.18, 0.68, 0.32),
    "pink_bloom_top": (0.18, 0.00, 0.36, 0.10),
    "water": (0.04, 0.68, 0.22, 0.86),
    "stone_path": (0.55, 0.72, 0.78, 0.88),
    "mushroom_red": (0.72, 0.78, 0.88, 0.92),
    "boat_gold": (0.08, 0.58, 0.22, 0.70),
    "window_glow": (0.26, 0.52, 0.34, 0.60),
}
lines.append("REGIONS")
px = im.load()
for name, (l, t, r, b) in regions.items():
    xs0, ys0 = int(l * w), int(t * h)
    xs1, ys1 = int(r * w), int(b * h)
    bucket = []
    step = max(1, (xs1 - xs0) // 24)
    for y in range(ys0, ys1, step):
        for x in range(xs0, xs1, step):
            bucket.append(px[x, y])
    if not bucket:
        continue
    med = tuple(sorted(c[i] for c in bucket)[len(bucket) // 2] for i in range(3))
    # also mean
    mean = tuple(sum(c[i] for c in bucket) // len(bucket) for i in range(3))
    lines.append(f"{name:18} median={hex_of(med)} mean={hex_of(mean)} n={len(bucket)}")

lines.append("GRID")
cols, rows = 8, 6
for gy in range(rows):
    row_bits = []
    for gx in range(cols):
        x0, x1 = gx * w // cols, (gx + 1) * w // cols
        y0, y1 = gy * h // rows, (gy + 1) * h // rows
        bucket = []
        step = max(1, (x1 - x0) // 16)
        for y in range(y0, y1, step):
            for x in range(x0, x1, step):
                bucket.append(px[x, y])
        mean = tuple(sum(c[i] for c in bucket) // len(bucket) for i in range(3))
        row_bits.append(hex_of(mean))
    lines.append(f"r{gy} " + " ".join(row_bits))

# Full-frame hue families so small accents are not swallowed by 16-color quantize.
families = {
    "yellow_green": [],
    "leaf_green": [],
    "deep_green": [],
    "pale_highlight": [],
    "wood_tan": [],
    "bark": [],
    "terracotta": [],
    "salmon_pink": [],
    "purple": [],
    "blue_water": [],
    "gold": [],
    "red": [],
}
for y in range(0, h, 1):
    for x in range(0, w, 1):
        rgb = px[x, y]
        hh, ss, vv = hsv_of(rgb)
        deg = hh * 360
        if vv > 0.82 and ss < 0.22:
            families["pale_highlight"].append(rgb)
        elif 250 <= deg <= 325 and ss > 0.22 and vv > 0.28:
            families["purple"].append(rgb)
        elif 180 <= deg < 250 and ss > 0.18 and 0.25 < vv < 0.85:
            families["blue_water"].append(rgb)
        elif 70 <= deg < 105 and ss > 0.35 and vv > 0.45:
            families["yellow_green"].append(rgb)
        elif 105 <= deg < 155 and ss > 0.25 and vv > 0.40:
            families["leaf_green"].append(rgb)
        elif 80 <= deg < 160 and vv <= 0.42 and ss > 0.15:
            families["deep_green"].append(rgb)
        elif (deg >= 345 or deg < 18) and ss > 0.40 and vv > 0.45:
            families["red"].append(rgb)
        elif 8 <= deg < 28 and ss > 0.28 and vv > 0.62:
            families["salmon_pink"].append(rgb)
        elif 8 <= deg < 30 and ss > 0.30 and vv <= 0.62:
            families["terracotta"].append(rgb)
        elif 18 <= deg < 45 and ss > 0.35 and vv > 0.65:
            families["gold"].append(rgb)
        elif 22 <= deg < 50 and 0.25 < ss <= 0.55 and 0.45 < vv <= 0.85:
            families["wood_tan"].append(rgb)
        elif 10 <= deg < 40 and vv <= 0.40 and ss > 0.20:
            families["bark"].append(rgb)

def median_rgb(bucket):
    if not bucket:
        return None
    return tuple(sorted(c[i] for c in bucket)[len(bucket) // 2] for i in range(3))

lines.append("FAMILIES")
pix_total = w * h
for name, bucket in families.items():
    med = median_rgb(bucket)
    if med is None:
        lines.append(f"{name:18} n=0")
        continue
    lines.append(
        f"{name:18} n={len(bucket):6d} pct={100*len(bucket)/pix_total:5.1f} median={hex_of(med)}"
    )

out = Path(r"assets/skill_20261110/style_lock/palette_sample.txt")
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
