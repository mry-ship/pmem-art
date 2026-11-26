"""Shared pad / stop / reflow policy for daily converge + V8 batch runners (no API deps)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from .judge_rules import (  # noqa: F401  moved to judge_rules, re-exported
    DEFAULT_ANATOMY_FLOOR,
    NON_ANATOMY_RUBRICS,
    SCENE_COLLAPSE_FLOOR,
    STYLE_INFLATION_IGNORE,
    _ALREADY_FIXED,
    _CLAUSE_SPLIT,
    _COLLAPSE_MARKERS,
    _DIRECT_NEGATION,
    _NEG_GAP,
    _PURE_FIX,
    _SPECIFIC_FIX_MARKERS,
    _STILL_BROKEN,
    _STYLE_BREAK_MARKERS,
    _STYLE_FAMILY_KEYS,
    _STYLE_SCENE_FLOOR,
    _WEAK_FIX_MARKERS,
    _clause_around,
    _gap_is_filler,
    _mentioned,
    _tip_pushes_volume,
    anatomy_ok_for_stop,
    anatomy_score,
    anatomy_score_loose,
    clone_subject_structure_ok_for_stop,
    coerce_dims_dict,
    collapse_marked,
    dim_float,
    infer_style_family,
    next_fix_is_weak,
    reconcile_fix_with_subject,
    reflow_fix_text,
    rewrite_reflow_by_dims,
    scene_structure_ok_for_stop,
    style_body_floor,
    style_break_marked,
    style_scene_floor,
    ui_shell_structure_ok_for_stop,
)

DEFAULT_PAD_MODE = "auto"
# Kept so older imports still resolve. Mild perspective is no longer rewritten
# upward: a 6.x score stays inside the harmonic mean.
SCENE_MILD_PERSPECTIVE_CREDIT = 8.5
SCENE_MILD_CREDIT_MIN = 6.0
# Alias of the collapse floor. Older imports still resolve.
SCENE_STRUCTURE_FLOOR = 6.0
DEFAULT_PLATEAU_ROUNDS = 2
# Match skill docs / v2fix: R4+ consecutive drop >0.5 early-stop.
DEFAULT_REGRESSION_DROP = 0.15
DEFAULT_AUTO_PAD_DROP = 0.2
DEFAULT_EARLY_STOP_MIN_ROUND = 2
# 安全早停默认关。要开时在 config 写 converge.safe_early_stop: true。
# 打开之后仍用 0.15 / 第 2 轮，不要改回 0.5 / 第 4 轮。
DEFAULT_SAFE_EARLY_STOP = False
PROMPT_CHAR_BUDGET = 3500












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
























def scene_perspective_credit(
    dims: dict[str, Any] | None,
    defects: str,
    weights: dict[str, Any] | None,
) -> tuple[float | None, str]:
    """No longer raises a scene score.

    A mild vanishing-point nit stays in the harmonic mean. Rewriting it to 8.5
    manufactured stops above 9.5. Collapse under 6.0 is handled by the hurdle.
    """
    del dims, defects, weights
    return None, ""














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


EARLY_STOP_REASONS = frozenset({"STOP_REGRESSION", "STOP_PLATEAU", "STOP_HURDLE_BOUND"})


def hurdle_still_blocks(hurdle: Any, score: float, threshold: float) -> bool:
    """True only when a hurdle dim actually hit and the official score is still under the line.

    A missing dimension is not a hit. ``apply_hurdles`` leaves the harmonic mean alone
    until a listed dim is strictly under its floor, then replaces the official score
    with that dim. Equality with the floor is not a hit.
    """
    return isinstance(hurdle, dict) and float(score) < float(threshold)


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
    safe_early_stop: bool = DEFAULT_SAFE_EARLY_STOP,
    subject_kind: str = "",
    defects: str = "",
    style_text: str = "",
    hurdle_blocks_target: bool = False,
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
    if not safe_early_stop:
        return None
    if round_num >= int(early_stop_min_round):
        if best_total is not None and total <= float(best_total) - float(regression_drop):
            return "STOP_REGRESSION"
        # 门槛维仍低于线时，正式分就是该维，再开一轮也到不了 9.5。
        if hurdle_blocks_target and total < float(threshold):
            return "STOP_HURDLE_BOUND"
        if no_improve_streak >= plateau_rounds:
            return "STOP_PLATEAU"
    return None
