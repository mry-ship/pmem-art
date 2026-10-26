"""Pure pad / stop / reflow policy for V8 skill converge (no API deps)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

DEFAULT_PAD_MODE = "ref"
DEFAULT_ANATOMY_FLOOR = 8.5
DEFAULT_PLATEAU_ROUNDS = 2
DEFAULT_REGRESSION_DROP = 0.3
DEFAULT_AUTO_PAD_DROP = 0.2
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


def anatomy_score(dims: dict[str, Any] | None) -> float | None:
    """Strict key for stop/floor gates (fail closed if missing)."""
    return dim_float(dims, "perspective_anatomy")


def anatomy_score_loose(dims: dict[str, Any] | None) -> float | None:
    """Alias-tolerant score for reflow tip ranking only."""
    return dim_float(dims, "perspective_anatomy", "perspective", "anatomy")


def rewrite_reflow_by_dims(
    base_prompt: str,
    *,
    defects: list[str] | None = None,
    dims: dict[str, Any] | None = None,
    api_scale: str = "medium",
    recompose_dir: str = "",
    max_fixes: int = 2,
) -> str:
    """Dimension-aware reflow: short fixes, no universal volume-light bandage."""
    base = (base_prompt or "").strip()
    fixes: list[str] = []
    raw = [str(d).strip() for d in (defects or []) if str(d or "").strip()]

    anat = anatomy_score_loose(dims)
    tex = dim_float(dims, "texture_detail", "texture")
    light = dim_float(dims, "lighting_color", "lighting")
    comp = dim_float(dims, "composition")

    anat_weak = anat is not None and anat < 8.5
    ranked: list[tuple[float, str]] = []
    if anat is not None:
        ranked.append((anat, "解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边"))
    if tex is not None:
        ranked.append((tex, "质感：锐化轮廓与材质分界，抑制融化边缘，勿用噪点冒充细节"))
    if light is not None:
        if anat_weak:
            ranked.append((light, "光影：理顺主光方向与明暗交接，勿用光效掩盖结构问题"))
        else:
            ranked.append((light, "光影：理顺主光方向与明暗交接，仅在需要时加强体积光"))
    if comp is not None:
        ranked.append((comp, "构图：稳住主体可读性与层次，勿新增冲突焦点"))
    ranked.sort(key=lambda x: x[0])

    # Reserve ≥1 slot for explicit defects/intent when present (dims tips must not starve them).
    ranked_cap = max(0, max_fixes - (1 if raw else 0))
    for _score, tip in ranked:
        if len(fixes) >= ranked_cap:
            break
        if anat_weak and "体积光" in tip:
            continue
        fixes.append(tip)

    for d in raw:
        if len(fixes) >= max_fixes:
            break
        if anat_weak and "体积光" in d:
            continue
        if d not in fixes:
            fixes.append(d[:80])

    if not fixes:
        if anat is not None and anat < 9.0:
            fixes.append("优先修复结构与边缘完整")
        elif tex is not None and tex < 9.0:
            fixes.append("优先恢复边缘锐度与材质区分")
        else:
            fixes.append("小步修正最低分维，保持原机位与身份")

    if (api_scale or "").lower() == "recompose" and recompose_dir and len(fixes) < max_fixes:
        cam = f"保持新机位：{recompose_dir}"
        if cam not in fixes:
            fixes.append(cam)

    base = re.sub(r"\s*\|\s*【回流修正】.*$", "", base).strip(" |")
    return f"{base} | 【回流修正】" + "；".join(fixes[:max_fixes])


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
    cur_anat = anatomy_score(current.get("dims"))
    if cur_anat is None or cur_anat < float(anatomy_floor):
        return best_round or current
    if best_round is None:
        return current
    br_anat = anatomy_score(best_round.get("dims"))
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
) -> str | None:
    """Return stop_reason or None to continue. Score failures never stop here."""
    if not score_ok or total is None:
        return None
    anat = anatomy_score(dims)
    # Missing anatomy dims must NOT unlock STOP_TARGET_REACHED (fail closed).
    # When anatomy blocks target, still allow plateau/regression below.
    if (
        total >= threshold
        and round_num >= min_rounds
        and anat is not None
        and anat >= anatomy_floor
    ):
        return "STOP_TARGET_REACHED"
    if best_total is not None and total <= float(best_total) - float(regression_drop):
        return "STOP_REGRESSION"
    if no_improve_streak >= plateau_rounds:
        return "STOP_PLATEAU"
    return None
