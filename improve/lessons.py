"""Weakness taxonomy and per-round lessons."""
from __future__ import annotations

import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

# ---------------------------------------------------------------------------
# Capability coach — 「本轮可学」 + practice plan + weakness categories
# ---------------------------------------------------------------------------

WEAKNESS_CATEGORIES: dict[str, list[str]] = {
    "composition": [r"构图", r"透视", r"重心", r"景别", r"三分法", r"对称", r"裁切", r"composition", r"perspective"],
    "lighting": [r"光影", r"光源", r"明暗", r"逆光", r"高光", r"阴影", r"色温", r"lighting", r"rim\s*light"],
    "anatomy": [r"头身", r"手指", r"手部", r"五官", r"关节", r"比例", r"解剖", r"anatomy", r"头太大"],
    "color_palette": [r"色板", r"脏色", r"霓虹", r"赛博", r"饱和", r"配色", r"palette", r"过饱和"],
    "line_edge": [r"描边", r"线宽", r"毛边", r"漏抠", r"边缘", r"杂边", r"line\s*weight", r"aliasing"],
    "ui_9slice": [r"九宫格", r"9[- ]?slice", r"中心拉伸", r"转角", r"状态族", r"normal/pressed"],
    "material": [r"材质", r"塑料感", r"油腻", r"金属", r"布料", r"水彩", r"笔触", r"material"],
    "narrative_camera": [r"叙事", r"镜头", r"机位", r"电影感", r"氛围", r"camera", r"cinematic"],
    "icon_consistency": [r"图标一致", r"stroke", r"viewBox", r"视觉重量", r"currentColor"],
    "style_lock": [r"画风漂移", r"风格不一致", r"混风", r"style\s*drift"],
}

DRILLS: dict[str, list[str]] = {
    "composition": [
        "练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板",
        "用简单色块缩略图先定重心，再进细节",
    ],
    "lighting": [
        "同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界",
        "只改光源方向重绘一轮，强制统一高光材质",
    ],
    "anatomy": [
        "手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离",
        "头身比尺规：在草图上标 7.5 头身刻度再细化",
    ],
    "color_palette": [
        "从模块 palette 抽 3 HEX 做限色练习，禁止引入霓虹辅色",
        "把上次红线里的脏色/霓虹写成 Negative，重跑 1 轮",
    ],
    "line_edge": [
        "透明底边缘检查：放大 200% 查毛边与漏抠",
        "统一描边宽度预设（如 1.5px round）整套重描",
    ],
    "ui_9slice": [
        "主面板只画九宫格线框 → 再填中心色，确认中心可双向拉伸",
        "按钮四态同系练习：只改明度/内阴影，不改外形轮廓",
    ],
    "material": [
        "同形不同材质：金属 / 布 / 陶瓷各一张，锁死高光形状",
        "去掉油腻高光：改用硬边分层或青瓷釉面高光",
    ],
    "narrative_camera": [
        "同一场景三种景别（远/中/特写）各一张，只改镜头语言",
        "Key Art：先写一句叙事再构图，主体动作靠前",
    ],
    "icon_consistency": [
        "5 枚图标同 viewBox/stroke 批量生成后做一致性审查表",
        "故意做一枚偏轻一枚偏重，再光学校正到同重量",
    ],
    "style_lock": [
        "对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习",
        "打开上次混风反例，列出 3 条禁止混入的风格词",
    ],
}


_DIM_LABEL_ONLY = re.compile(
    r"^(?:(?:构图|光影|色彩|透视|解剖|质感|肌理|细节|材质|风格|规格|结构)"
    r"(?:\s*[:：=]?\s*[0-9]+(?:\.[0-9]+)?)?(?:[/／,，、\s]+|$))+$"
)


def _is_dim_label_only(text: str) -> bool:
    s = (text or "").strip()
    return bool(s) and bool(_DIM_LABEL_ONLY.match(s))


def _drop_dim_label_clauses(text: str) -> str:
    parts = re.split(r"[\n；;]+", text or "")
    kept = [p.strip() for p in parts if p.strip() and not _is_dim_label_only(p.strip())]
    return "\n".join(kept)


def classify_weakness(text: str) -> list[str]:
    cats: list[str] = []
    for cat, pats in WEAKNESS_CATEGORIES.items():
        for pat in pats:
            if re.search(pat, text or "", re.I):
                cats.append(cat)
                break
    return cats


def craft_lessons_from_round(
    *,
    defects: str = "",
    strengths: str = "",
    next_fix: str = "",
    score: float = 0.0,
    dims: str = "",
) -> list[dict[str, str]]:
    """Return 1–3 concrete 「本轮可学」 craft tips tied to what was wrong/fixed."""
    lessons: list[dict[str, str]] = []
    defects_kept = _drop_dim_label_clauses(defects)
    blob = _drop_dim_label_clauses(f"{defects}\n{next_fix}")
    no_issue = bool(re.search(r"无明显|无硬伤|没有明显|无缺陷", defects_kept or "")) and not re.search(
        r"但是|但仍|仍|不足|错误|畸形|但|却|不过", defects_kept or ""
    )
    cats = [] if no_issue or not blob else classify_weakness(blob)
    if not cats and defects_kept and not no_issue:
        cats = ["style_lock"]
    seen: set[str] = set()
    for cat in cats:
        if cat in seen:
            continue
        seen.add(cat)
        drills = DRILLS.get(cat) or ["针对本轮缺陷做一次局部重绘练习"]
        tip = {
            "category": cat,
            "lesson": f"本轮短板偏「{cat}」：{ (defects or next_fix or '对照评分维度')[:80] }",
            "drill": drills[0],
            "from_score": str(score),
        }
        lessons.append(tip)
        if len(lessons) >= 3:
            break
    if strengths and len(lessons) < 3:
        lessons.append({
            "category": "keep",
            "lesson": f"保留本轮已做对的：{(strengths or '')[:80]}",
            "drill": "下一轮 Prompt 显式写入这些亮点作为正向锚点",
            "from_score": str(score),
        })
    return lessons[:3]


def print_round_lessons(lessons: list[dict[str, str]], *, silent: bool = False) -> None:
    if not lessons:
        return
    if silent:
        return
    print("📚 本轮可学（能力提升）:")
    for i, L in enumerate(lessons, 1):
        print(f"   {i}. [{L.get('category')}] {L.get('lesson')}")
        print(f"      → 练习: {L.get('drill')}")


