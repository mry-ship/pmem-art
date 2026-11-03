# -*- coding: utf-8 -*-
"""Draw measured slot boxes on original ref for visual QA of placements."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
REF = ROOT / "ref_new_full.jpg"
OUT = ROOT / "_measure_guide.png"

# Manual boxes from reading original 409x1024 farm scene (fractions)
# Order = z-order bottom to top
BOXES = [
    # id, left, top, right, bottom, color
    ("bg", 0.00, 0.00, 1.00, 1.00, (80, 80, 80)),
    ("barn", 0.02, 0.08, 0.58, 0.32, (180, 100, 40)),
    ("truck", 0.12, 0.22, 0.78, 0.42, (220, 40, 40)),
    ("shed", 0.48, 0.28, 0.98, 0.50, (40, 120, 200)),
    ("hay", 0.00, 0.38, 0.40, 0.54, (220, 180, 40)),
    ("tire_ice", 0.52, 0.48, 0.78, 0.58, (60, 160, 200)),
    ("trough", 0.55, 0.45, 0.95, 0.58, (200, 120, 40)),
    ("sheep", 0.04, 0.55, 0.88, 0.72, (240, 240, 240)),
    ("farmer", 0.22, 0.34, 0.58, 0.62, (40, 80, 180)),
    ("fence", 0.00, 0.62, 1.00, 0.80, (160, 120, 80)),
]

def main():
    ref = Image.open(REF).convert("RGBA")
    W, H = ref.size
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for name, l, t, r, b, col in BOXES:
        x0, y0, x1, y1 = int(l * W), int(t * H), int(r * W), int(b * H)
        draw.rectangle([x0, y0, x1, y1], outline=col + (255,), width=2)
        draw.text((x0 + 3, y0 + 3), name, fill=col + (255,))
    out = Image.alpha_composite(ref, overlay)
    # also make a 2x for readability
    out2 = out.resize((W * 2, H * 2), Image.Resampling.NEAREST)
    out2.convert("RGB").save(OUT)
    print("wrote", OUT, "base", W, H)

if __name__ == "__main__":
    main()
