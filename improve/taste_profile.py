"""Taste profile, paths, and feedback→taste updates."""
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

from .project_library import (
    DEFAULT_TASTE,
    PROFILE_DIR,
    REFLECTIONS_DIR,
    TASTE_FILE,
    ensure_project_library_bound,
    slugify_project_id,
    sync_active_project_to_library,
)

def _mem_root(root: Path) -> Path:
    return root / ".memory-art"


def reflections_dir(root: Path) -> Path:
    d = _mem_root(root) / REFLECTIONS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def profile_dir(root: Path) -> Path:
    d = _mem_root(root) / PROFILE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def taste_path(root: Path) -> Path:
    return profile_dir(root) / TASTE_FILE


def load_taste(root: Path) -> dict[str, Any]:
    meta = ensure_project_library_bound(root)
    p = taste_path(root)
    if not p.is_file():
        taste = json.loads(json.dumps(DEFAULT_TASTE))
        taste["project_id"] = meta.get("project_id") or slugify_project_id(root.name)
        taste["project_name"] = meta.get("project_name") or root.name
        taste["layer_scope"] = "private"
        taste["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
        return taste
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    out = json.loads(json.dumps(DEFAULT_TASTE))
    out.update({k: v for k, v in data.items() if k in out or k.startswith("_") or k in ("project_id", "project_name", "layer_scope")})
    out["project_id"] = meta.get("project_id") or out.get("project_id") or slugify_project_id(root.name)
    out["project_name"] = meta.get("project_name") or out.get("project_name") or root.name
    out["layer_scope"] = "private"
    for k, v in DEFAULT_TASTE["signal_counts"].items():
        out.setdefault("signal_counts", {})
        out["signal_counts"].setdefault(k, v)
    return out


def save_taste(root: Path, taste: dict[str, Any]) -> Path:
    meta = ensure_project_library_bound(root)
    taste = dict(taste)
    taste["project_id"] = meta.get("project_id") or slugify_project_id(root.name)
    taste["project_name"] = meta.get("project_name") or root.name
    taste["layer_scope"] = "private"
    taste["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    p = taste_path(root)
    p.write_text(json.dumps(taste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_active_project_to_library(root)
    return p


def _uniq_append(lst: list[Any], item: str, limit: int = 40) -> list[Any]:
    item = (item or "").strip()
    if not item:
        return lst
    # de-dupe case-insensitive for short phrases
    low = item.lower()
    existing = [x for x in lst if isinstance(x, str) and x.lower() != low]
    existing.append(item)
    return existing[-limit:]


# ---------------------------------------------------------------------------
# Taste updates from feedback phrases
# ---------------------------------------------------------------------------

LIGHTING_HINTS = [
    (r"侧逆光|rim\s*light", "侧逆光 / rim light"),
    (r"顶光|顶光硬", "顶光"),
    (r"柔光|柔和光|soft\s*light", "柔光"),
    (r"电影感|cinematic", "电影感光影"),
    (r"黄金时刻|golden\s*hour|黄昏光", "黄金时刻光"),
    (r"冷光源|冷光", "冷光源"),
    (r"暖光|暖色光", "暖光"),
]
COMPOSITION_HINTS = [
    (r"三分法|rule\s*of\s*thirds", "三分法构图"),
    (r"居中|居中构图|对称", "居中/对称构图"),
    (r"特写|close[- ]?up", "特写"),
    (r"半身|bust", "半身"),
    (r"全身|full\s*body", "全身"),
    (r"宽幅|海报构图|电影画幅", "宽幅/海报构图"),
]
LINE_HINTS = [
    (r"细线|细描边|1\.5px|thin\s*line", "细线/轻描边"),
    (r"粗线|粗描边|bold\s*line|2\.5px", "粗线/重描边"),
    (r"无描边|无线稿|lineless", "无描边"),
]
TEMP_HINTS = [
    (r"冷色|冷色调|cool", "冷色调"),
    (r"暖色|暖色调|warm", "暖色调"),
    (r"青瓷白|墨蓝|鎏金", "青瓷白+墨蓝+鎏金倾向"),
    (r"高饱和|过饱和", "避免过饱和"),
    (r"低饱和|莫兰迪", "低饱和/莫兰迪"),
]
BAN_HINTS = [
    (r"太赛博|赛博|霓虹紫|霓虹", "赛博霓虹/霓虹紫"),
    (r"头太大|头身不对|幼态头身|头身比", "错误头身比/头过大"),
    (r"过曝|爆高光|高光过曝", "过曝高光"),
    (r"塑料感|油腻高光", "廉价塑料感/油腻高光"),
    (r"脏暗|脏色", "脏暗阴影/脏色"),
    (r"漏抠|黑底|毛边", "漏抠/黑底/毛边"),
    (r"手指粘连|六指|手部崩坏", "手部崩坏/手指粘连"),
]


def _extract_hints(text: str, table: list[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    for pat, label in table:
        if re.search(pat, text, re.I):
            found.append(label)
    return found


def clip_phrase(text: str, max_len: int) -> str:
    """Trim to max_len without cutting mid-clause; prefer last punctuation / space."""
    t = (text or "").strip()
    if max_len <= 0 or len(t) <= max_len:
        return t
    window = t[:max_len]
    for sep in ("。", "；", "！", "？", "，", "、", ";", ",", " ", "\n"):
        i = window.rfind(sep)
        if i >= max(8, max_len // 3):
            return window[: i + (1 if sep in "。；！？，、" else 0)].rstrip("，、,; ")
    # No good break — drop a dangling half-word/CJK char cluster at the end.
    return window.rstrip()



# Soft / non-actionable defect phrases that must not enter banned_habits
_SOFT_DEFECT_EXACT = frozenset({"微瑕", "几乎无", "几乎无瑕", "无明显问题", "无", "无硬伤", "无明显瑕疵"})


def is_soft_defect_phrase(text: str) -> bool:
    """True for junk soft summaries like 避免「微瑕」/「几乎无」/empty 避免「」/可再* polish."""
    s = (text or "").strip()
    if not s:
        return True

    def _core_soft(x: str) -> bool:
        x = (x or "").strip()
        if not x:
            return True
        if x in _SOFT_DEFECT_EXACT:
            return True
        if x.startswith("几乎无") and len(x) <= 12:
            return True
        if x.startswith("无硬伤") and len(x) <= 10:
            return True
        if x == "微瑕" or (x.startswith("微瑕") and len(x) <= 6):
            return True
        if "可再" in x and len(x) <= 16 and not any(k in x for k in ("漏", "黑底", "毛边", "霓虹", "抠")):
            return True
        if re.fullmatch(r"(微瑕|几乎无|几乎无瑕)", x):
            return True
        return False

    if _core_soft(s):
        return True
    m = re.search(r"避免「([^」]*)」", s)
    if m and _core_soft(m.group(1)):
        return True
    # full redline summary that is ONLY soft inside 避免「…」
    m2 = re.search(r"避免「([^」]*)」\s*$", s)
    if m2 and _core_soft(m2.group(1)):
        return True
    return False


def apply_feedback_to_taste(
    root: Path,
    text: str,
    kind: str,
) -> dict[str, Any]:
    """Strengthen taste profile from keep/reject/style phrases. Returns updated taste."""
    taste = load_taste(root)
    sc = taste.setdefault("signal_counts", {})
    t = text.strip()

    if kind == "recipe":
        sc["keeps"] = int(sc.get("keeps", 0)) + 1
        taste["keep_phrases"] = _uniq_append(taste.get("keep_phrases") or [], clip_phrase(t, 80))
        for h in _extract_hints(t, LIGHTING_HINTS):
            taste["preferred_lighting"] = _uniq_append(taste.get("preferred_lighting") or [], h)
        for h in _extract_hints(t, COMPOSITION_HINTS):
            taste["preferred_composition"] = _uniq_append(taste.get("preferred_composition") or [], h)
        for h in _extract_hints(t, LINE_HINTS):
            taste["preferred_line_weight"] = _uniq_append(taste.get("preferred_line_weight") or [], h)
        for h in _extract_hints(t, TEMP_HINTS):
            taste["preferred_color_temperature"] = _uniq_append(taste.get("preferred_color_temperature") or [], h)
    elif kind == "style_redline":
        sc["rejects"] = int(sc.get("rejects", 0)) + 1
        taste["reject_phrases"] = _uniq_append(taste.get("reject_phrases") or [], clip_phrase(t, 80))
        if not is_soft_defect_phrase(t):
            for h in _extract_hints(t, BAN_HINTS):
                if not is_soft_defect_phrase(h):
                    taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)
            # raw short reject also becomes banned habit (skip soft junk)
            if len(t) <= 40:
                taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], t)
    elif kind in ("visual_correction", "art_decision"):
        sc["style_fixes"] = int(sc.get("style_fixes", 0)) + 1
        taste["style_notes"] = _uniq_append(taste.get("style_notes") or [], clip_phrase(t, 100))
        for h in _extract_hints(t, LIGHTING_HINTS + COMPOSITION_HINTS + LINE_HINTS + TEMP_HINTS):
            # route into the right bucket
            if h in [x[1] for x in LIGHTING_HINTS]:
                taste["preferred_lighting"] = _uniq_append(taste.get("preferred_lighting") or [], h)
            elif h in [x[1] for x in COMPOSITION_HINTS]:
                taste["preferred_composition"] = _uniq_append(taste.get("preferred_composition") or [], h)
            elif h in [x[1] for x in LINE_HINTS]:
                taste["preferred_line_weight"] = _uniq_append(taste.get("preferred_line_weight") or [], h)
            elif h in [x[1] for x in TEMP_HINTS]:
                taste["preferred_color_temperature"] = _uniq_append(taste.get("preferred_color_temperature") or [], h)
        for h in _extract_hints(t, BAN_HINTS):
            if not is_soft_defect_phrase(h):
                taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)

    # Drop any soft junk that snuck in from older paths
    taste["banned_habits"] = [
        h for h in (taste.get("banned_habits") or []) if not is_soft_defect_phrase(str(h))
    ]

    save_taste(root, taste)
    return taste



