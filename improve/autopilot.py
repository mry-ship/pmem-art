"""Whisper tip budget, silent autopilot, and coach."""
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

from .taste_profile import (
    BAN_HINTS,
    _extract_hints,
    load_taste,
    profile_dir,
    save_taste,
)
from .reflection import list_reflections, write_session_reflection
from .lessons import WEAKNESS_CATEGORIES, classify_weakness, craft_lessons_from_round

# ---------------------------------------------------------------------------
# Whisper Autopilot — invisible self-improve by default（静默自动驾驶）
# ---------------------------------------------------------------------------

CATEGORY_TIP_ZH: dict[str, str] = {
    "composition": "构图",
    "lighting": "光影",
    "anatomy": "结构/手部",
    "color_palette": "色板",
    "line_edge": "边缘/描边",
    "ui_9slice": "九宫格",
    "material": "材质高光",
    "narrative_camera": "镜头叙事",
    "icon_consistency": "图标一致性",
    "style_lock": "画风锁定",
    "keep": "保留亮点",
}

TIP_BUDGET_FILE = "tip_budget.json"


def tip_budget_path(root: Path) -> Path:
    return profile_dir(root) / TIP_BUDGET_FILE


def _load_tip_budget(root: Path) -> dict[str, Any]:
    p = tip_budget_path(root)
    if not p.is_file():
        return {"sessions_tipped": {}, "updated_at": ""}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"sessions_tipped": {}, "updated_at": ""}


def try_consume_tip_budget(root: Path, session_key: str) -> bool:
    """At most 1 tip per session finish (or feedback burst key). Returns True if tip allowed."""
    key = (session_key or "latest").strip() or "latest"
    bud = _load_tip_budget(root)
    tipped = bud.setdefault("sessions_tipped", {})
    if tipped.get(key):
        return False
    tipped[key] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    # prune old keys (keep last 40)
    if len(tipped) > 40:
        for k in sorted(tipped.keys())[:-40]:
            tipped.pop(k, None)
    bud["updated_at"] = tipped[key]
    tip_budget_path(root).write_text(json.dumps(bud, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def _short_phrase(text: str, n: int = 18) -> str:
    """Trim to n chars; strip leading negations so '不要'+phrase won't double-negate."""
    t = re.sub(r"\s+", "", (text or "").strip())
    t = re.sub(r"^(别再|不要再|别|不要|别太|别这么|别这样|禁止|严禁)", "", t)
    t = t.strip("，。,.！!：:；;、 ")
    return t[:n] if t else ""




def compose_whisper_tip(
    *,
    lessons: list[dict[str, str]] | None = None,
    defects: str = "",
    strengths: str = "",
    taste_changes: list[str] | None = None,
    banned_new: list[str] | None = None,
    score_jump: float | None = None,
    winner_passed: bool | None = None,
    feedback_kind: str = "",
    feedback_text: str = "",
) -> str | None:
    """One-line 「小提示」. Prefer remember/redline, else next-time focus. None if nothing useful."""
    lessons = lessons or []
    taste_changes = taste_changes or []
    banned_new = banned_new or []

    # 0) Explicit feedback wins (highest signal, shortest phrase)
    if feedback_kind == "style_redline" and feedback_text:
        hits = _extract_hints(feedback_text, BAN_HINTS)
        phrase = _short_phrase(hits[0], 16) if hits else _short_phrase(feedback_text, 16)
        phrase = phrase or "这条红线"
        return f"「小提示」已记住：不要{phrase}"
    if feedback_kind == "recipe" and feedback_text:
        phrase = _short_phrase(feedback_text, 16) or "这版"
        return f"「小提示」已记住：留着「{phrase}」"
    if feedback_kind in ("visual_correction", "art_decision") and feedback_text:
        hits = _extract_hints(feedback_text, BAN_HINTS)
        if hits:
            return f"「小提示」已记住：不要{_short_phrase(hits[0], 16)}"
        phrase = _short_phrase(feedback_text, 16)
        if phrase:
            return f"「小提示」下次注意：{phrase}"

    def _clean_ban(raw: str) -> str | None:
        # Prefer BAN_HINTS extractions; skip long memory-summary junk
        hits = _extract_hints(raw, BAN_HINTS)
        if hits:
            return _short_phrase(hits[0], 16)
        short = _short_phrase(raw, 16)
        if not short or len(raw) > 40 or "收敛" in raw or "避免「" in raw:
            return None
        return short

    def _session_focus() -> str | None:
        # Prefer concrete ban/defect phrase, then category label
        blob = " ".join(
            [defects or ""]
            + [str(L.get("lesson") or "") for L in lessons if (L.get("category") or "") != "keep"]
        )
        hits = _extract_hints(blob, BAN_HINTS)
        if hits:
            return f"「小提示」下次注意：{_short_phrase(hits[0], 14)}"
        for L in lessons:
            cat = L.get("category") or ""
            if cat and cat != "keep":
                label = CATEGORY_TIP_ZH.get(cat, cat)
                return f"「小提示」下次注意：{label}"
        cats = classify_weakness(defects or "")
        if cats:
            label = CATEGORY_TIP_ZH.get(cats[0], cats[0])
            return f"「小提示」下次注意：{label}"
        if defects:
            phrase = _short_phrase(defects, 14)
            if phrase:
                return f"「小提示」下次注意：{phrase}"
        return None

    # 1) This-session focus (converge finish) — beats global banned noise
    if not feedback_kind:
        focus = _session_focus()
        if focus:
            return focus

    # 2) Newly remembered ban / redline (from taste delta / feedback)
    for b in banned_new:
        phrase = _clean_ban(b)
        if phrase:
            return f"「小提示」已记住：不要{phrase}"

    # 3) Taste change remember
    for ch in taste_changes:
        if "banned_habits" in ch:
            bit = ch.split(":", 1)[-1].strip().lstrip("+").strip()
            phrase = _clean_ban(bit.split(",")[0])
            if phrase:
                return f"「小提示」已记住：不要{phrase}"
        if "preferred_" in ch:
            bit = ch.split(":", 1)[-1].strip().lstrip("+").strip()
            phrase = _short_phrase(bit.split(",")[0], 14)
            if phrase and len(bit.split(",")[0]) <= 40:
                return f"「小提示」已记住：偏爱{phrase}"

    # 4) Score jump celebration (quiet)
    if score_jump is not None and score_jump >= 1.0 and winner_passed:
        return f"「小提示」这轮跳了 +{score_jump:.1f}，口味已悄悄变强"

    # 5) Fallback session focus (e.g. feedback path with defects)
    focus = _session_focus()
    if focus:
        return focus
    return None


def run_silent_autopilot(
    root: Path,
    data: dict[str, Any],
    *,
    session_id: str = "latest",
    lessons: list[dict[str, str]] | None = None,
    defects: str = "",
    strengths: str = "",
    winner: dict[str, Any] | None = None,
    rounds: list[dict[str, Any]] | None = None,
    source: str = "converge_finish",
    feedback_kind: str = "",
    feedback_text: str = "",
    force_tip: bool = False,
    enqueue_learn: int = 2,
) -> dict[str, Any]:
    """
    Invisible self-improve: update taste, strengthen from reflections, quietly stash
    1–2 learn proposals. Returns tip (or None) under tip budget (≤1 per session).
    """
    lessons = lessons or []
    winner = winner or {}
    rounds = rounds or []

    from .improve_cmds import run_improve_pass
    from .knowledge import propose_breadth_expansions
    report = run_improve_pass(root, data, last_n=20, apply=True)
    proposals: list[dict[str, Any]] = []
    if enqueue_learn > 0:
        try:
            proposals = propose_breadth_expansions(root, data, limit=enqueue_learn)
            if proposals:
                stash = profile_dir(root) / "learn_proposals.json"
                stash.write_text(
                    json.dumps(
                        {
                            "proposals": proposals,
                            "at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
                            "source": source,
                            "silent": True,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
        except Exception:
            proposals = []

    # detect newly banned from taste_changes
    banned_new: list[str] = []
    for ch in report.get("taste_changes") or []:
        if "banned_habits" in str(ch):
            bit = str(ch).split(":", 1)[-1].strip().lstrip("+").strip()
            for part in bit.split(","):
                part = part.strip()
                if part:
                    banned_new.append(part)

    score_jump = None
    if rounds and winner.get("score") is not None:
        try:
            scores = [float(r.get("score", 0)) for r in rounds]
            if len(scores) >= 2:
                score_jump = float(winner["score"]) - min(scores)
        except (TypeError, ValueError):
            score_jump = None

    tip = compose_whisper_tip(
        lessons=lessons,
        defects=defects or str(winner.get("defects") or ""),
        strengths=strengths or str(winner.get("strengths") or ""),
        taste_changes=list(report.get("taste_changes") or []),
        banned_new=banned_new,
        score_jump=score_jump,
        winner_passed=bool(winner.get("passed")) if winner else None,
        feedback_kind=feedback_kind,
        feedback_text=feedback_text,
    )

    tip_emitted = None
    budget_key = f"{source}:{session_id}"
    if tip and (force_tip or try_consume_tip_budget(root, budget_key)):
        tip_emitted = tip
    elif tip and not force_tip:
        tip_emitted = None  # budget exhausted — stay quiet

    # sidecar for agents / peek
    side = {
        "ran_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
        "source": source,
        "session_id": session_id,
        "tip": tip_emitted,
        "tip_candidate": tip,
        "taste_changes": report.get("taste_changes") or [],
        "learn_queued": [p.get("id") for p in proposals],
        "avg_winner_score": report.get("avg_winner_score"),
    }
    (profile_dir(root) / "last_autopilot.json").write_text(
        json.dumps(side, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "tip": tip_emitted,
        "report": report,
        "proposals": proposals,
        "sidecar": side,
    }


def print_whisper_tip(tip: str | None) -> None:
    if tip:
        print(tip)


def build_coach_plan(
    root: Path,
    data: dict[str, Any],
    *,
    last_n: int = 20,
) -> dict[str, Any]:
    """Turn redlines + reflections into a personal practice plan."""
    refs = list_reflections(root, limit=last_n)
    cat_counter: Counter[str] = Counter()
    for ref in refs:
        weak = str(ref.get("what_still_weak") or "")
        for d in (ref.get("taste_deltas") or {}).get("from_defects") or []:
            weak += " " + str(d)
        for fix in ref.get("what_fixed") or []:
            weak += " " + str(fix)
        for cat in classify_weakness(weak):
            cat_counter[cat] += 1
        # also from scores history lessons if stored
        for lesson in ref.get("lessons") or []:
            if isinstance(lesson, dict) and lesson.get("category") and lesson["category"] != "keep":
                cat_counter[str(lesson["category"])] += 1

    for e in data.get("entries") or []:
        if e.get("kind") == "style_redline":
            for cat in classify_weakness(str(e.get("summary") or "")):
                cat_counter[cat] += 1

    top = cat_counter.most_common(5)
    weak_spots = [{"category": c, "hits": n, "drills": DRILLS.get(c, [])[:2]} for c, n in top]
    next_goals = []
    for spot in weak_spots[:3]:
        next_goals.append({
            "draw_goal": f"下一张专门练「{spot['category']}」：{ (spot['drills'] or ['局部重绘'])[0] }",
            "category": spot["category"],
        })

    # Capability trend: compare older half vs newer half of reflections
    trend: dict[str, Any] = {}
    if len(refs) >= 4:
        mid = len(refs) // 2
        newer, older = refs[:mid], refs[mid:]
        def _cat_counts(rs: list[dict]) -> Counter[str]:
            c: Counter[str] = Counter()
            for ref in rs:
                blob = str(ref.get("what_still_weak") or "")
                for d in (ref.get("taste_deltas") or {}).get("from_defects") or []:
                    blob += " " + str(d)
                for cat in classify_weakness(blob):
                    c[cat] += 1
            return c
        cn, co = _cat_counts(newer), _cat_counts(older)
        declining = []
        rising = []
        all_cats = set(cn) | set(co)
        for cat in all_cats:
            # refs are newest-first: fewer hits in newer = declining weakness (good)
            if cn[cat] < co[cat]:
                declining.append(cat)
            elif cn[cat] > co[cat]:
                rising.append(cat)
        trend = {"declining_weaknesses": declining, "rising_weaknesses": rising, "note": "newer vs older half of reflections"}

    plan = {
        "schema": "pmem-art.coach.v1",
        "built_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
        "reflections_scanned": len(refs),
        "weak_spots": weak_spots,
        "next_draw_goals": next_goals,
        "capability_trend": trend,
        "encouragement": (
            "短板在下降，保持 warm-start + 每轮「本轮可学」闭环。"
            if trend.get("declining_weaknesses")
            else "先集中打磨 Top1 短板，再扩知识广度。"
        ),
    }
    out = profile_dir(root) / "coach_plan.json"
    out.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return plan


def cmd_coach(root: Path, data: dict[str, Any], *, last_n: int = 20) -> int:
    plan = build_coach_plan(root, data, last_n=last_n)
    print("🎓 `/pmem-coach` 个人能力教练计划\n")
    print(f"   · 扫描反思: {plan.get('reflections_scanned')} 份")
    if plan.get("weak_spots"):
        print("   · 短板排序（弱 → 练）:")
        for i, w in enumerate(plan["weak_spots"], 1):
            print(f"      {i}. {w['category']}（命中 {w['hits']}）")
            for d in (w.get("drills") or [])[:2]:
                print(f"         → {d}")
    else:
        print("   · 暂无足够短板信号（多跑几次 converge 后再来）")
    if plan.get("next_draw_goals"):
        print("   · 下一张可画目标:")
        for g in plan["next_draw_goals"]:
            print(f"      · {g['draw_goal']}")
    trend = plan.get("capability_trend") or {}
    if trend.get("declining_weaknesses"):
        print(f"   · 能力进步：这些短板在下降 → {', '.join(trend['declining_weaknesses'])}")
    if trend.get("rising_weaknesses"):
        print(f"   · 需关注：这些短板在上升 → {', '.join(trend['rising_weaknesses'])}")
    print(f"\n   · 计划已写入: .memory-art/_profile/coach_plan.json")
    print(f"   · {plan.get('encouragement')}")
    return 0

