"""Confident App Icon geometry checks. Uncertain measurements do not change the score."""
from __future__ import annotations

import re
from pathlib import Path

# 单独的 1024 是画幅，不是图标。必须出现图标身份词才测量。
_ICON_TASK = re.compile(
    r"app\s*icon|appicon|桌面图标|启动图标|应用图标|商店图标|icon\.a",
    re.I,
)
# Well under the 72% safe-zone floor so soft glow and borderline spans still go to the judge.
_CONFIDENT_SPAN = 0.62
_BG_AGREE = 42.0
_FG_DIST = 55.0


def _looks_like_app_icon(goal: str, module: str) -> bool:
    return bool(_ICON_TASK.search(f"{module or ''} {goal or ''}"))


def _dist(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def icon_geometry_skip_reason(
    image_path: str | Path,
    *,
    goal: str = "",
    module: str = "",
) -> str:
    """Return a reason when the symbol is confidently too small for an App Icon.

    Empty means: not an icon task, the file cannot be measured, or the span is
    large enough that the normal judge must still run.
    """
    if not _looks_like_app_icon(goal, module):
        return ""
    path = Path(image_path) if image_path else Path()
    if not path.is_file():
        return ""
    try:
        from PIL import Image

        img = Image.open(path).convert("RGB")
    except (OSError, ValueError):
        return ""
    w, h = img.size
    if w < 64 or h < 64 or abs((w / h) - 1.0) > 0.08:
        return ""
    side = 96
    small = img.resize((side, side))
    px = small.load()
    corners: list[tuple[float, float, float]] = []
    for x0, y0 in ((0, 0), (side - 5, 0), (0, side - 5), (side - 5, side - 5)):
        acc = [0.0, 0.0, 0.0]
        n = 0
        for y in range(y0, y0 + 5):
            for x in range(x0, x0 + 5):
                r, g, b = px[x, y]
                acc[0] += r
                acc[1] += g
                acc[2] += b
                n += 1
        corners.append((acc[0] / n, acc[1] / n, acc[2] / n))
    for i, a in enumerate(corners):
        for b in corners[i + 1 :]:
            if _dist(a, b) > _BG_AGREE:
                return ""
    bg = (
        sum(c[0] for c in corners) / 4.0,
        sum(c[1] for c in corners) / 4.0,
        sum(c[2] for c in corners) / 4.0,
    )
    min_x, min_y, max_x, max_y = side, side, -1, -1
    fg = 0
    for y in range(side):
        for x in range(side):
            if _dist(px[x, y], bg) <= _FG_DIST:
                continue
            fg += 1
            if x < min_x:
                min_x = x
            if y < min_y:
                min_y = y
            if x > max_x:
                max_x = x
            if y > max_y:
                max_y = y
    if fg < int(side * side * 0.04) or max_x < min_x:
        return ""
    span_w = (max_x - min_x + 1) / side
    span_h = (max_y - min_y + 1) / side
    if max(span_w, span_h) >= _CONFIDENT_SPAN:
        return ""
    return (
        f"几何早停：符号跨度 {span_w:.0%}×{span_h:.0%}，明显低于 72% 安全区，"
        "跳过远程审图，安全区按 7.2 计"
    )


def cap_dims_for_icon_geometry(
    image_path: str | Path,
    dims: str,
    *,
    goal: str = "",
    module: str = "",
) -> tuple[str, str]:
    """Force 安全区 7.2 when geometry confidently fails. Other scores stay."""
    reason = icon_geometry_skip_reason(image_path, goal=goal, module=module)
    if not reason:
        return dims or "", ""
    text = dims or ""
    new, n = re.subn(r"(安全区)\s*[0-9]+(?:\.[0-9]+)?", r"\g<1>7.2", text, count=1)
    if n == 0:
        new = (text.rstrip() + " 安全区7.2").strip()
    return new, reason
