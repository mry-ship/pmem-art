"""Shared pad / stop / reflow policy for daily converge + V8 batch runners (no API deps)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_PAD_MODE = "auto"
DEFAULT_ANATOMY_FLOOR = 7.5
# Scenes share perspective_anatomy with characters. A score under this is treated as
# collapsed structure. Between this and the character floor, only collapse language blocks stop.
SCENE_COLLAPSE_FLOOR = 4.0
# Mild scene perspective is credited up to this when weighting, so a 5.9 vanishing-point
# nit does not pull an otherwise finished plate under 9.6. The raw score stays on the card.
SCENE_MILD_PERSPECTIVE_CREDIT = 8.5
# Only a high-but-not-collapsed perspective (5.9) is reweighted. 4.2 stays a real miss.
SCENE_MILD_CREDIT_MIN = 5.5
# Kept so older imports still resolve. Scene stop no longer uses 6.0 as a cutoff.
SCENE_STRUCTURE_FLOOR = 6.0
NON_ANATOMY_RUBRICS = frozenset({"skill_additive_5d", "ui_5d", "app_icon_5d"})
_COLLAPSE_MARKERS = (
    "结构崩",
    "结构塌",
    "体块散",
    "透视崩溃",
    "透视崩",
    "几何崩",
    "融成一团",
    "结构散架",
    "边缘融化",
    "结构融化",
    "collapsed geometry",
    "structure collapsed",
    "perspective collapsed",
    "melting into",
)
_COLLAPSE_NEGATION = ("禁止", "不要", "勿", "别", "不是", "并非", "没有", "无", "not ", "no ")
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


def collapse_marked(text: str) -> bool:
    """True when defects describe a collapsed structure, not a prohibition against one."""
    raw = text or ""
    low = raw.lower()
    for marker in _COLLAPSE_MARKERS:
        start = 0
        needle = marker.lower()
        while True:
            idx = low.find(needle, start)
            if idx < 0:
                break
            prefix = low[max(0, idx - 6) : idx]
            if any(neg in prefix for neg in _COLLAPSE_NEGATION):
                start = idx + len(needle)
                continue
            return True
    return False


def scene_structure_ok_for_stop(
    dims: dict[str, Any] | None,
    defects: str = "",
) -> bool:
    """Scene stop: missing dim fails closed; under 4.0 or collapse language blocks; a mild 5.9 may pass."""
    anat = anatomy_score(dims)
    if anat is None:
        return False
    if anat < SCENE_COLLAPSE_FLOOR:
        return False
    if collapse_marked(defects):
        return False
    return True


def scene_perspective_credit(
    dims: dict[str, Any] | None,
    defects: str,
    weights: dict[str, Any] | None,
) -> tuple[float | None, str]:
    """Reweight a mild scene perspective score so it does not sink an otherwise finished total.

    Returns (adjusted_weighted, warning). (None, "") means leave the audited total alone.
    The stored dimension stays at the raw value.
    """
    parsed = coerce_dims_dict(dims)
    anat = anatomy_score(parsed)
    if anat is None or parsed is None or "perspective_anatomy" not in parsed:
        return None, ""
    if anat >= SCENE_MILD_PERSPECTIVE_CREDIT or anat < SCENE_MILD_CREDIT_MIN:
        return None, ""
    if collapse_marked(defects):
        return None, ""
    w = weights or {}
    credited = dict(parsed)
    credited["perspective_anatomy"] = SCENE_MILD_PERSPECTIVE_CREDIT
    keys = [k for k in credited if k in w]
    if len(keys) < 4:
        return None, ""
    total = sum(float(credited[k]) * float(w.get(k) or 0) for k in keys)
    warn = (
        f"场景透视 {anat:.1f} 属轻微偏差（未写结构塌缩），"
        f"加权时这一维按 {SCENE_MILD_PERSPECTIVE_CREDIT} 计，原始分仍保留"
    )
    return round(total, 2), warn


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
    """Pick pad image for the *next* round."""
    m = (mode or DEFAULT_PAD_MODE).lower().strip()
    if m == "previous":
        return current_out if score_ok else ref
    if m == "auto":
        if not score_ok or total is None:
            return ref
        # New high (or first score): chain. Big drop: force ref. Slight drop: keep chain.
        if best_total is None or total >= float(best_total):
            return current_out
        if total < float(best_total) - float(auto_drop):
            return ref
        return current_out
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
) -> bool:
    """Whether a historical best plate is safe to chain under pad=auto (fail-closed on missing anat)."""
    m = (pad_mode or DEFAULT_PAD_MODE).lower().strip()
    if m == "previous":
        return True
    if m == "ref":
        return False
    if (subject_kind or "").strip().lower() == "scene":
        anat = anatomy_score(dims)
        # A 4.2 plate is not a mild nit. Don't chain it. 5.9 and above can chain.
        if anat is None or anat < SCENE_MILD_CREDIT_MIN:
            return False
        return not collapse_marked(defects)
    return anatomy_ok_for_stop(dims, anatomy_floor)


def pick_best_round_on_stop(
    *,
    stop_reason: str,
    best_round: dict[str, Any] | None,
    current: dict[str, Any],
    anatomy_floor: float,
) -> dict[str, Any]:
    """On STOP_TARGET, prefer anatomy-OK rounds; otherwise keep historical max total."""
    if stop_reason != "STOP_TARGET_REACHED":
        return best_round or current
    cur_dims = coerce_dims_dict(current.get("dims"))
    cur_anat = anatomy_score(cur_dims)
    if cur_anat is None or cur_anat < float(anatomy_floor):
        return best_round or current
    if best_round is None:
        return current
    br_dims = coerce_dims_dict(best_round.get("dims"))
    br_anat = anatomy_score(br_dims)
    if br_anat is None or br_anat < float(anatomy_floor):
        return current
    if float(current.get("total") or 0) >= float(best_round.get("total") or 0):
        return current
    return best_round


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
) -> str | None:
    """Return stop_reason or None to continue. Score failures never stop here."""
    if not score_ok or total is None:
        return None
    anat = anatomy_score(dims)
    # Missing anatomy dims must NOT unlock STOP_TARGET_REACHED (fail closed).
    # When anatomy blocks target, still allow plateau/regression below (after min early-stop round).
    if (
        total >= threshold
        and round_num >= min_rounds
        and anat is not None
        and anat >= anatomy_floor
    ):
        return "STOP_TARGET_REACHED"
    if round_num >= int(early_stop_min_round):
        if best_total is not None and total <= float(best_total) - float(regression_drop):
            return "STOP_REGRESSION"
        if no_improve_streak >= plateau_rounds:
            return "STOP_PLATEAU"
    return None
