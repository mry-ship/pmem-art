"""Shared pad / stop / reflow policy for daily converge + V8 batch runners (no API deps)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_PAD_MODE = "auto"
DEFAULT_ANATOMY_FLOOR = 7.5
# Scenes share perspective_anatomy with characters. A score under this is treated as
# collapsed structure. Between this and the character floor, only collapse language blocks stop.
# Under this, a scene is structurally collapsed and cannot stop.
# The official score then becomes min(harmonic mean, this dimension).
SCENE_COLLAPSE_FLOOR = 6.0
# Kept so older imports still resolve. Mild perspective is no longer rewritten
# upward: a 6.x score stays inside the harmonic mean.
SCENE_MILD_PERSPECTIVE_CREDIT = 8.5
SCENE_MILD_CREDIT_MIN = 6.0
# Alias of the collapse floor. Older imports still resolve.
SCENE_STRUCTURE_FLOOR = 6.0
NON_ANATOMY_RUBRICS = frozenset(
    {"skill_additive_5d", "ui_5d", "app_icon_5d", "icon_prop_5d", "icon_svg_5d"}
)
_COLLAPSE_MARKERS = (
    "结构崩",
    "结构塌",
    "体块散",
    "透视崩溃",
    "透视崩",
    "几何崩",
    "融成一团",
    "融化",
    "结构散架",
    "塌缩",
    "边缘融化",
    "结构融化",
    "collapsed geometry",
    "structure collapsed",
    "perspective collapsed",
    "melting into",
)
_NEG_GAP = {"", "的", "地", "得", "使用", "用", "任何", "再", "去", "低", "高", "画"}
DEFAULT_PLATEAU_ROUNDS = 2
# Match skill docs / v2fix: R4+ consecutive drop >0.5 early-stop.
DEFAULT_REGRESSION_DROP = 0.5
DEFAULT_AUTO_PAD_DROP = 0.2
DEFAULT_EARLY_STOP_MIN_ROUND = 4
PROMPT_CHAR_BUDGET = 3500


def dim_float(dims: dict[str, Any] | None, *keys: str) -> float | None:
    if not isinstance(dims, dict):
        return None
    for k in keys:
        if k not in dims:
            continue
        try:
            return float(dims[k])
        except (TypeError, ValueError):
            continue
    return None


def coerce_dims_dict(dims: Any) -> dict[str, Any] | None:
    """Accept dims_parsed dict, or a nested {'parsed': {...}} audit blob."""
    if not isinstance(dims, dict):
        return None
    if "perspective_anatomy" in dims or "composition" in dims:
        return dims
    nested = dims.get("parsed")
    if isinstance(nested, dict):
        return nested
    return dims


def anatomy_score(dims: dict[str, Any] | None) -> float | None:
    """Strict key for stop/floor gates (fail closed if missing)."""
    return dim_float(coerce_dims_dict(dims), "perspective_anatomy")


def anatomy_score_loose(dims: dict[str, Any] | None) -> float | None:
    """Alias-tolerant score for reflow tip ranking only."""
    return dim_float(coerce_dims_dict(dims), "perspective_anatomy", "perspective", "anatomy")


def anatomy_ok_for_stop(
    dims: dict[str, Any] | None,
    anatomy_floor: float = DEFAULT_ANATOMY_FLOOR,
) -> bool:
    """Fail-closed: missing perspective_anatomy cannot unlock STOP_TARGET."""
    anat = anatomy_score(dims)
    return anat is not None and anat >= float(anatomy_floor)


_SCALE_LOCK_MARKERS = (
    "尺度",
    "比例失调",
    "比例偏",
    "比例不对",
    "比例过",
    "头身",
    "偏小",
    "偏大",
    "过小",
    "过大",
    "太小",
    "太大",
    "略小",
    "略大",
    "仍小",
    "仍大",
    "偏窄",
    "过窄",
    "太窄",
    "偏短",
    "过短",
    "巩膜",
    "黑点瞳",
    "独眼",
    "sclera",
    "cyclops",
    "black-dot",
    "black dot pupil",
    "relative scale",
    "out of scale",
    "out of proportion",
    "too small",
    "too large",
)
_SCALE_LOCK_NEGATION = re.compile(
    r"(?:禁止|不要|勿|别|不是|并非|没有|无|禁|not\s|no\s)[\s\S]{0,4}$",
    re.IGNORECASE,
)


def _scale_clause(text: str, index: int) -> str:
    start = 0
    for i, ch in enumerate(text[:index]):
        if ch in "，。；,.;":
            start = i + 1
    end = len(text)
    for i in range(index, len(text)):
        if text[i] in "，。；,.;":
            end = i
            break
    return text[start:end]


def _scale_clause_resolved(clause: str) -> bool:
    """A clause that already says the scale/eye issue is fixed is not a lock."""
    if any(k in clause for k in ("仍", "还", "依旧", "未达", "不合格", "不正确")):
        return False
    return any(k in clause for k in ("合格", "正确", "已解决", "已修复", "已放大", "已修好"))


def scale_lock_marked(text: str) -> bool:
    """True when defects are relative scale, proportion, or eye grammar.

    Chaining that plate locks the bug. Negated or already-fixed clauses do not count.
    """
    raw = text or ""
    low = raw.lower()
    for marker in _SCALE_LOCK_MARKERS:
        start = 0
        needle = marker.lower()
        while True:
            idx = low.find(needle, start)
            if idx < 0:
                break
            prefix = low[max(0, idx - 12) : idx]
            if _SCALE_LOCK_NEGATION.search(prefix):
                start = idx + len(needle)
                continue
            if _scale_clause_resolved(_scale_clause(low, idx)):
                start = idx + len(needle)
                continue
            return True
    return False


_CLAUSE_SPLIT = set("，。；、,;！？!?\n")
_STILL_BROKEN = (
    "没有解决", "没解决", "未解决", "还没解决", "尚未解决", "待解决",
    "无法解决", "没能解决", "未能解决", "需要解决", "不解决",
    "不是已经解决", "没有已经解决", "并非已经解决", "不是已解决", "并未已经解决",
)
_ALREADY_FIXED = ("已经解决", "已解决", "解决了")
_PURE_FIX = re.compile(r"^(?:已经解决了?|已解决了?|解决了|已修复了?|已消除了?)$")
_DIRECT_NEGATION = ("不要", "不用", "并不", "别用", "不是", "并非", "没有", "禁止", "未出现", "勿", "不", "非")


def _clause_around(low: str, idx: int, key_len: int) -> tuple[str, str]:
    """Text before the hit, and the whole clause. Commas, pauses, and 但 split clauses."""
    start = 0
    for i in range(idx - 1, -1, -1):
        if low[i] in _CLAUSE_SPLIT or low[i] == "但":
            start = i + 1
            break
    end = len(low)
    for j in range(idx + key_len, len(low)):
        if low[j] in _CLAUSE_SPLIT or low[j] == "但":
            end = j
            break
    return low[start:idx], low[start:end]


def collapse_marked(text: str) -> bool:
    """True when defects describe a collapsed structure, not a prohibition against one."""
    low = (text or "").lower()
    return any(_mentioned(low, marker, as_break=True) for marker in _COLLAPSE_MARKERS)


def scene_structure_ok_for_stop(
    dims: dict[str, Any] | None,
    defects: str = "",
    floor: float | None = None,
) -> bool:
    """Scene stop: missing dim fails closed. Collapse or a real break blocks.

    A low perspective number is left to the harmonic mean. `floor` is kept for callers.
    """
    del floor
    anat = anatomy_score(dims)
    if anat is None:
        return False
    if collapse_marked(defects):
        return False
    return True


# Special media are scored against their own ruler. A low lighting or proportion
# score is not the same miss as a melted joint. Break language cancels the tolerance.
_STYLE_FAMILY_KEYS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pixel", ("像素风", "像素画", "像素", "pixel art", "pixel-art", "点阵", "8-bit", "8bit", "16-bit", "16bit")),
    ("chibi", ("q版", "chibi", "二头身", "三头身", "大头娃娃", "sd比例")),
    ("iso", ("等轴", "轴测", "正交", "isometric", "orthographic")),
    ("graphic", ("剪影", "剪纸", "皮影", "papercut", "paper-cut")),
    ("flat", ("扁平", "平涂", "矢量", "vector", "赛璐璐", "cel-shad", "cel shad", "cel shading")),
    ("wash", ("水彩", "水墨", "速写", "粉彩", "线稿", "浮世绘", "pastel", "watercolor")),
)
_STYLE_SCENE_FLOOR = {"iso": 5.5}
STYLE_INFLATION_IGNORE = {
    "pixel": {"平光", "颗粒太均匀", "数字化", "数字化噪点", "数字化痕迹", "数字化滤镜"},
    "flat": {"平光", "颗粒太均匀"},
    "wash": {"数字化", "数字化噪点", "数字化痕迹", "数字化滤镜"},
    "graphic": {"平光"},
}
_STYLE_BREAK_MARKERS = (
    "融化", "断肢", "粘连", "多手", "三只手", "六指", "关节断", "多指",
    "extra hand", "fused finger", "melted",
)


def _gap_is_filler(gap: str) -> bool:
    """True when the words between a negation and the keyword are only fillers."""
    rest = gap.strip()
    pieces = sorted((p for p in _NEG_GAP if p), key=len, reverse=True)
    while rest:
        for piece in pieces:
            if rest.startswith(piece):
                rest = rest[len(piece) :]
                break
        else:
            return False
    return True


def _mentioned(blob: str, needle: str, *, as_break: bool = False) -> bool:
    """True when needle is present and this clause is not a negation or an already-fixed note.

    Style words ignore 「解决」. Only a break marker is cleared by 已解决 / 解决了.
    """
    low = blob.lower()
    key = needle.lower()
    start = 0
    while True:
        idx = low.find(key, start)
        if idx < 0:
            return False
        if key == "像素" and low[idx + len(key) : idx + len(key) + 1] == "级":
            start = idx + len(key)
            continue
        prev = low[idx - 1 : idx] if idx else ""
        if key == "像素" and low[idx + len(key) : idx + len(key) + 2] in {"画质", "画面"}:
            start = idx + len(key)
            continue
        if key == "像素" and prev in {"高", "低", "超", "万"}:
            start = idx + len(key)
            continue
        if key in {"像素画", "像素风"} and low[idx + len(key) : idx + len(key) + 1] in {"质", "面"}:
            start = idx + len(key)
            continue
        if key in {"像素画", "像素风"} and prev in {"高", "超", "万"}:
            start = idx + len(key)
            continue
        if key in {"8-bit", "8bit", "16-bit", "16bit"} and prev.isdigit():
            start = idx + len(key)
            continue
        before, same = _clause_around(low, idx, len(key))
        if as_break and any(s in same for s in _STILL_BROKEN):
            return True
        if as_break and re.search(r"(?:不是|没有|并非|并未).{0,12}解决", same):
            return True
        if as_break and re.search(
            r"(?:解决了|已经解决|已解决|已修复).{0,6}(?:不了|又出现|又不|没有|不|没|吗)",
            same,
        ):
            return True
        if as_break and any(s in same for s in _ALREADY_FIXED):
            start = idx + len(key)
            continue
        tail = before[-12:]
        if "是不是" in tail or "有没有" in tail:
            return True
        negated = False
        for n in _DIRECT_NEGATION:
            pos = tail.rfind(n)
            if pos < 0:
                continue
            if _gap_is_filler(tail[pos + len(n) :].strip()):
                negated = True
                break
        if negated:
            start = idx + len(key)
            continue
        end = idx + len(key)
        while end < len(low) and low[end] not in _CLAUSE_SPLIT and low[end] != "但":
            end += 1
        if end < len(low) and (low[end] in _CLAUSE_SPLIT or low[end] == "但"):
            nxt = low[end + 1 :]
            for ch in _CLAUSE_SPLIT:
                if ch == "但":
                    continue
                cut = nxt.find(ch)
                if cut >= 0:
                    nxt = nxt[:cut]
            nxt_s = nxt.strip()
            if nxt_s.startswith("但是"):
                nxt_s = nxt_s[2:].strip()
            elif nxt_s.startswith("但") or nxt_s.startswith("是"):
                nxt_s = nxt_s[1:].strip()
            if _PURE_FIX.match(nxt_s):
                start = idx + len(key)
                continue
        return True


def infer_style_family(*parts: str) -> str:
    """pixel / chibi / iso / graphic / flat / wash / standard. From the brief, not the critique."""
    blob = " ".join(str(p or "") for p in parts)
    for name, keys in _STYLE_FAMILY_KEYS:
        if any(_mentioned(blob, k, as_break=False) for k in keys):
            return name
    return "standard"


def style_break_marked(text: str) -> bool:
    """A real structural break, not a medium that is supposed to look simple."""
    if collapse_marked(text):
        return True
    low = (text or "").lower()
    for marker in _STYLE_BREAK_MARKERS:
        if _mentioned(low, marker, as_break=True):
            return True
    return False


def style_body_floor(family: str, defects: str = "", requested: float = DEFAULT_ANATOMY_FLOOR) -> float:
    """人物、动物、机械一律用这条线。媒介不再把 7.5 打折。"""
    del family, defects
    return float(requested)


def style_scene_floor(
    family: str,
    requested: float = SCENE_COLLAPSE_FLOOR,
    defects: str = "",
) -> float:
    if abs(float(requested) - SCENE_COLLAPSE_FLOOR) > 1e-6:
        return float(requested)
    if style_break_marked(defects):
        return SCENE_COLLAPSE_FLOOR
    return float(_STYLE_SCENE_FLOOR.get(family, SCENE_COLLAPSE_FLOOR))


def scene_perspective_credit(
    dims: dict[str, Any] | None,
    defects: str,
    weights: dict[str, Any] | None,
) -> tuple[float | None, str]:
    """No longer raises a scene score.

    A mild vanishing-point nit stays in the harmonic mean. Rewriting it to 8.5
    manufactured stops above 9.6. Collapse under 6.0 is handled by the hurdle.
    """
    del dims, defects, weights
    return None, ""


def _tip_pushes_volume(tip: str) -> bool:
    low = (tip or "").lower()
    return "体积光" in tip or "volumetric" in low


def rewrite_reflow_by_dims(
    base_prompt: str,
    *,
    defects: list[str] | None = None,
    dims: dict[str, Any] | None = None,
    api_scale: str = "medium",
    recompose_dir: str = "",
    max_fixes: int = 2,
    lang: str = "en",
) -> str:
    """Dimension-aware reflow. Default language is English because this string is sent to the image model.

    Pass ``lang='zh'`` for the line shown to the artist. The two wordings are the same clause.
    """
    from .subject_lexicon import clause

    base = (base_prompt or "").strip()
    fixes: list[str] = []
    raw = [str(d).strip() for d in (defects or []) if str(d or "").strip()]

    anat = anatomy_score_loose(dims)
    tex = dim_float(coerce_dims_dict(dims), "texture_detail", "texture")
    light = dim_float(coerce_dims_dict(dims), "lighting_color", "lighting")
    comp = dim_float(coerce_dims_dict(dims), "composition")

    anat_weak = anat is not None and anat < 8.5
    ranked: list[tuple[float, str]] = []
    if anat is not None:
        ranked.append((anat, clause("anatomy", lang)))
    if tex is not None:
        ranked.append((tex, clause("texture", lang)))
    if light is not None:
        ranked.append((light, clause("light_weak" if anat_weak else "light_ok", lang)))
    if comp is not None:
        ranked.append((comp, clause("composition", lang)))
    ranked.sort(key=lambda x: x[0])

    # Reserve ≥1 slot for explicit defects/intent when present (dims tips must not starve them).
    ranked_cap = max(0, max_fixes - (1 if raw else 0))
    for _score, tip in ranked:
        if len(fixes) >= ranked_cap:
            break
        if anat_weak and _tip_pushes_volume(tip):
            continue
        fixes.append(tip)

    for d in raw:
        if len(fixes) >= max_fixes:
            break
        if anat_weak and _tip_pushes_volume(d):
            continue
        if d not in fixes:
            fixes.append(d[:80])

    if not fixes:
        if anat is not None and anat < 9.0:
            fixes.append(clause("fallback_structure", lang))
        elif tex is not None and tex < 9.0:
            fixes.append(clause("fallback_texture", lang))
        else:
            fixes.append(clause("fallback_small", lang))

    if (api_scale or "").lower() == "recompose" and recompose_dir and len(fixes) < max_fixes:
        cam = clause("camera", lang, dir=recompose_dir)
        if cam not in fixes:
            fixes.append(cam)

    base = re.sub(r"\s*\|\s*【回流修正】.*$", "", base).strip(" |")
    return f"{base} | 【回流修正】" + "；".join(fixes[:max_fixes])


_WEAK_FIX_MARKERS = (
    "加强氛围",
    "提升氛围",
    "提升体积光",
    "加强体积光",
    "提升质感",
    "提升细节",
    "微调局部",
    "保持原图",
    "已达标",
)
_SPECIFIC_FIX_MARKERS = ("手", "眼", "关节", "腕", "灭点", "边缘", "描边", "瞳", "蹄", "翼", "指")


def next_fix_is_weak(text: str) -> bool:
    """True when the proposed fix is empty or atmosphere boilerplate."""
    t = (text or "").strip()
    if not t or "已达标" in t:
        return True
    if len(t) < 8:
        return True
    if any(k in t for k in _WEAK_FIX_MARKERS) and not any(k in t for k in _SPECIFIC_FIX_MARKERS):
        return True
    return False


def reconcile_fix_with_subject(
    text: str,
    subject_kind: str,
    dims: dict[str, Any] | None = None,
) -> str:
    """Keep a specific fix. Replace it only when it fights the subject, or pushes volume light over a weak structure."""
    from .subject_lexicon import clause

    t = (text or "").strip()
    if not t:
        return t
    kind = (subject_kind or "").strip().lower()
    if kind == "scene" and any(k in t for k in ("关节", "双肘", "瞳孔", "握持", "手足", "pupils", "elbow")):
        return clause("scene_fix", "zh")
    if kind == "creature" and any(k in t for k in ("双眼瞳孔", "双肩双肘", "瞳孔同向")):
        return clause("creature_fix", "zh")
    if kind == "mechanical" and any(k in t for k in ("双眼瞳孔", "双肩双肘", "瞳孔同向", "pupils")):
        return clause("mech_fix", "zh")
    anat = anatomy_score_loose(dims)
    if anat is not None and anat < 8.5 and _tip_pushes_volume(t):
        t = t.replace("加强体积光", "理顺主光方向").replace("提升体积光", "理顺主光方向")
        t = re.sub(r"体积光", "主光方向", t)
        t = re.sub(r"volumetric light", "the key light", t, flags=re.I)
    return t


def reflow_fix_text(
    *,
    defects: list[str] | None = None,
    dims: dict[str, Any] | None = None,
    api_scale: str = "medium",
    recompose_dir: str = "",
    intent: str = "",
    max_fixes: int = 2,
    lang: str = "zh",
) -> str:
    """Daily-judge helper. Default Chinese is the line shown to the artist; pass lang='en' for the prompt."""
    raw = [str(d).strip() for d in (defects or []) if str(d or "").strip()]
    extra = (intent or "").strip()
    if extra and not next_fix_is_weak(extra) and extra not in raw:
        raw.append(extra)
    rewritten = rewrite_reflow_by_dims(
        "BASE",
        defects=raw,
        dims=dims,
        api_scale=api_scale,
        recompose_dir=recompose_dir,
        max_fixes=max_fixes,
        lang=lang,
    )
    if "【回流修正】" in rewritten:
        return rewritten.split("【回流修正】", 1)[-1].strip()
    return rewritten.strip()


def truncate_prompt(prompt: str, budget: int = PROMPT_CHAR_BUDGET) -> str:
    """Prefer dropping reflow tail over goal/recompose head when over budget."""
    p = prompt or ""
    if budget <= 0:
        return ""
    if len(p) <= budget:
        return p
    if "【回流修正】" in p:
        head, _sep, tail = p.partition("【回流修正】")
        head = head.rstrip(" |")
        prefix = head + " | 【回流修正】"
        room = budget - len(prefix)
        if room >= 24:
            return (prefix + tail[:room])[:budget]
        return head[:budget]
    return p[:budget]


def choose_next_pad(
    *,
    mode: str,
    ref: Path,
    current_out: Path,
    score_ok: bool,
    total: float | None,
    best_total: float | None,
    auto_drop: float = DEFAULT_AUTO_PAD_DROP,
) -> Path:
    """Pick pad image for the *next* round.

    auto and ref always return the original reference. previous chains the
    current plate only when that round scored. Fixes belong in the prompt.
    """
    del total, best_total, auto_drop
    m = (mode or DEFAULT_PAD_MODE).lower().strip()
    if m == "previous":
        return current_out if score_ok else ref
    return ref


def should_force_ref_pad(
    *,
    pad_mode: str,
    total: float | None,
    threshold: float,
    dims: dict[str, Any] | None,
    anatomy_floor: float,
) -> bool:
    """Force style_ref when high total but anatomy missing/low — except pad=previous."""
    if (pad_mode or "").lower().strip() == "previous":
        return False
    if total is None or total < float(threshold):
        return False
    anat = anatomy_score(dims)
    return anat is None or anat < float(anatomy_floor)


def plate_safe_to_pad(
    *,
    pad_mode: str,
    dims: dict[str, Any] | None,
    anatomy_floor: float = DEFAULT_ANATOMY_FLOOR,
    subject_kind: str = "",
    defects: str = "",
    goal: str = "",
    module: str = "",
    ref_image: str = "",
    ref_analysis: str = "",
) -> bool:
    """pad=auto and pad=ref never chain a generated plate. Only pad=previous may."""
    del dims, anatomy_floor, subject_kind, defects, goal, module, ref_image, ref_analysis
    return (pad_mode or DEFAULT_PAD_MODE).lower().strip() == "previous"


def ui_shell_structure_ok_for_stop(
    *,
    goal: str = "",
    ref_analysis: str = "",
    module: str = "",
    defects: str = "",
    dims: dict[str, Any] | None = None,
) -> bool:
    """Fail-closed for Clone UI popup shells: echo in content zone blocks STOP."""
    from .subject_lexicon import ui_shell_clone_task, ui_shell_echo_marked

    if not ui_shell_clone_task(goal=goal, ref_analysis=ref_analysis, module=module):
        return True
    if ui_shell_echo_marked(defects):
        return False
    parsed = coerce_dims_dict(dims)
    if parsed:
        nine = dim_float(parsed, "nine_slice_structure")
        if nine is not None and nine < 8.5:
            return False
        comp = dim_float(parsed, "composition")
        if comp is not None and comp < 8.5:
            return False
    return True


def clone_subject_structure_ok_for_stop(
    *,
    goal: str = "",
    ref_analysis: str = "",
    module: str = "",
    ref_image: str = "",
    defects: str = "",
    dims: dict[str, Any] | None = None,
) -> bool:
    """Fail-closed for Mode B icon/character: reference prop echo blocks STOP/pad/winner."""
    from .subject_lexicon import (
        clone_style_lock_new_subject_task,
        clone_subject_echo_marked,
    )

    if not clone_style_lock_new_subject_task(
        goal=goal,
        ref_analysis=ref_analysis,
        module=module,
        ref_image=ref_image,
    ):
        return True
    if clone_subject_echo_marked(defects):
        return False
    return True


def round_passes_structure_gates(
    *,
    goal: str = "",
    ref_analysis: str = "",
    module: str = "",
    ref_image: str = "",
    defects: str = "",
    dims: dict[str, Any] | None = None,
) -> bool:
    """Combined UI shell + clone subject gates for finish winner selection."""
    if not ui_shell_structure_ok_for_stop(
        goal=goal,
        ref_analysis=ref_analysis,
        module=module,
        defects=defects,
        dims=dims,
    ):
        return False
    return clone_subject_structure_ok_for_stop(
        goal=goal,
        ref_analysis=ref_analysis,
        module=module,
        ref_image=ref_image,
        defects=defects,
        dims=dims,
    )


def pick_best_round_on_stop(
    *,
    stop_reason: str,
    best_round: dict[str, Any] | None,
    current: dict[str, Any],
    anatomy_floor: float,
    subject_kind: str = "",
    style_text: str = "",
) -> dict[str, Any]:
    """On STOP_TARGET, prefer anatomy-OK rounds; otherwise keep historical max total."""
    if stop_reason != "STOP_TARGET_REACHED":
        return best_round or current
    family = infer_style_family(style_text) if style_text else "standard"

    def _broken(row: dict[str, Any] | None) -> bool:
        if not row:
            return False
        raw = row.get("defects") or ""
        if isinstance(raw, list):
            raw = "；".join(str(x) for x in raw)
        return style_break_marked(str(raw))

    cur_broken = _broken(current)
    best_broken = _broken(best_round)
    if cur_broken and not best_broken and best_round is not None:
        return best_round
    if best_broken and not cur_broken:
        return current

    def _row_defects(row: dict[str, Any] | None) -> str:
        if not row:
            return ""
        raw = row.get("defects") or ""
        if isinstance(raw, list):
            raw = "；".join(str(x) for x in raw)
        return str(raw)

    def _row_floor(row: dict[str, Any] | None) -> float:
        text = _row_defects(row)
        if subject_kind == "scene":
            return style_scene_floor(family, defects=text)
        return style_body_floor(family, text, float(anatomy_floor))

    floor = _row_floor(current)
    cur_dims = coerce_dims_dict(current.get("dims"))
    cur_anat = anatomy_score(cur_dims)
    cur_is_rubric = bool(
        cur_dims
        and "perspective_anatomy" not in cur_dims
        and any(k in cur_dims for k in _UI_ICON_DIM_KEYS)
    )
    # Scenes ignore the old numeric perspective line. Collapse text still loses.
    if subject_kind == "scene":
        if cur_anat is None or collapse_marked(_row_defects(current)):
            return best_round or current
    elif not cur_is_rubric and (cur_anat is None or cur_anat < floor):
        return best_round or current
    if best_round is None:
        return current
    br_dims = coerce_dims_dict(best_round.get("dims"))
    br_anat = anatomy_score(br_dims)
    br_is_rubric = bool(
        br_dims
        and "perspective_anatomy" not in br_dims
        and any(k in br_dims for k in _UI_ICON_DIM_KEYS)
    )
    if subject_kind == "scene":
        if br_anat is None or collapse_marked(_row_defects(best_round)):
            return current
    elif not br_is_rubric and (br_anat is None or br_anat < _row_floor(best_round)):
        return current
    if float(current.get("total") or 0) >= float(best_round.get("total") or 0):
        return current
    return best_round


_UI_ICON_DIM_KEYS = (
    "nine_slice_structure",
    "glyph_silhouette",
    "squircle_safe_zone",
    "rgba_pipeline_compliance",
    "state_suite_cohesion",
    "silhouette",
    "alpha",
    "no_text",
    "stroke_consistency",
    "recognizability",
)


def target_dims_allow_stop(
    dims: dict[str, Any] | None,
    anatomy_floor: float,
    *,
    subject_kind: str = "",
    defects: str = "",
    style_text: str = "",
) -> bool:
    """Body subjects need anatomy >= floor. Scenes use the 6.0 collapse line. UI/icon have their own hurdles."""
    parsed = coerce_dims_dict(dims) or {}
    family = infer_style_family(style_text) if style_text else "standard"
    if parsed and "perspective_anatomy" not in parsed and any(k in parsed for k in _UI_ICON_DIM_KEYS):
        floors = {
            "nine_slice_structure": 7.5,
            "rgba_pipeline_compliance": 8.0,
            "glyph_silhouette": 8.0,
            "squircle_safe_zone": 8.0,
            "silhouette": 8.0,
            "alpha": 8.0,
            "no_text": 8.0,
            "stroke_consistency": 8.0,
            "recognizability": 8.0,
        }
        for key, floor in floors.items():
            if key not in parsed:
                continue
            try:
                val = float(parsed[key])
            except (TypeError, ValueError):
                return False
            if val < floor:
                return False
        if "flawlessness" not in parsed:
            return False
        try:
            if float(parsed["flawlessness"]) <= 0:
                return False
        except (TypeError, ValueError):
            return False
        return True
    craft = {"composition", "lighting_color", "perspective_anatomy", "texture_detail", "spec_style"}
    if craft <= set(parsed) and "flawlessness" not in parsed:
        return False
    if subject_kind == "scene":
        return scene_structure_ok_for_stop(
            parsed, defects, floor=style_scene_floor(family, defects=defects)
        )
    floor = style_body_floor(family, defects, float(anatomy_floor))
    anat = anatomy_score(parsed)
    return anat is not None and anat >= floor


def decide_round_stop(
    *,
    score_ok: bool,
    total: float | None,
    dims: dict[str, Any] | None,
    round_num: int,
    min_rounds: int,
    threshold: float,
    anatomy_floor: float,
    best_total: float | None,
    no_improve_streak: int,
    plateau_rounds: int = DEFAULT_PLATEAU_ROUNDS,
    regression_drop: float = DEFAULT_REGRESSION_DROP,
    early_stop_min_round: int = DEFAULT_EARLY_STOP_MIN_ROUND,
    subject_kind: str = "",
    defects: str = "",
    style_text: str = "",
) -> str | None:
    """Return stop_reason or None to continue. Score failures never stop here."""
    if not score_ok or total is None:
        return None
    # Missing anatomy on a person must NOT unlock STOP_TARGET_REACHED.
    # Scenes stop on the 6.0 collapse line. UI / icon dims carry their own hurdles.
    if (
        total >= threshold
        and round_num >= min_rounds
        and target_dims_allow_stop(
            dims,
            anatomy_floor,
            subject_kind=subject_kind,
            defects=defects,
            style_text=style_text,
        )
    ):
        return "STOP_TARGET_REACHED"
    if round_num >= int(early_stop_min_round):
        if best_total is not None and total <= float(best_total) - float(regression_drop):
            return "STOP_REGRESSION"
        if no_improve_streak >= plateau_rounds:
            return "STOP_PLATEAU"
    return None
