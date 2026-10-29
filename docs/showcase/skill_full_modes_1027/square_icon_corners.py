"""Force App Icon master to full-bleed sharp 90-degree corners."""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from PIL import Image

SRC = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets\skill_icon_a_r5.jpg"
)
OUT = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets\skill_icon_a_r6.jpg"
)


def dist(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum(abs(a[i] - b[i]) for i in range(3))


def main() -> None:
    im = Image.open(SRC).convert("RGB").resize((1024, 1024), Image.Resampling.LANCZOS)
    px = im.load()
    w, h = im.size
    m = int(w * 0.08)
    ring = []
    for x in range(m, w - m):
        ring.append(px[x, m])
        ring.append(px[x, h - 1 - m])
    for y in range(m, h - m):
        ring.append(px[m, y])
        ring.append(px[w - 1 - m, y])
    bg = Counter(ring).most_common(1)[0][0]
    canvas = im.copy()
    px2 = canvas.load()
    r = 56
    for cx, cy, dx, dy in (
        (0, 0, 1, 1),
        (w - 1, 0, -1, 1),
        (0, h - 1, 1, -1),
        (w - 1, h - 1, -1, -1),
    ):
        for i in range(r + 2):
            for j in range(r + 2):
                x = cx + dx * i
                y = cy + dy * j
                if not (0 <= x < w and 0 <= y < h):
                    continue
                outside = i * i + j * j > (r - 10) * (r - 10)
                near_edge = i < 4 or j < 4
                p = px2[x, y]
                if near_edge or (outside and (dist(p, bg) > 18 or min(p) > 220)):
                    px2[x, y] = bg
    for x in range(w):
        px2[x, 0] = bg
        px2[x, h - 1] = bg
    for y in range(h):
        px2[0, y] = bg
        px2[w - 1, y] = bg
    canvas.save(OUT, quality=95)
    print(f"wrote {OUT} bg={bg}")


if __name__ == "__main__":
    main()
