"""improve / progress / taste CLI commands."""
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
    COMPOSITION_HINTS,
    LIGHTING_HINTS,
    TEMP_HINTS,
    _extract_hints,
    _uniq_append,
    is_soft_defect_phrase,
    load_taste,
    profile_dir,
    save_taste,
    taste_path,
)
from .reflection import list_reflections
from .warm_start import rank_memory_entry
from .lessons import classify_weakness

# ---------------------------------------------------------------------------
# Improve pass + progress
# ---------------------------------------------------------------------------

def run_improve_pass(
    root: Path,
    data: dict[str, Any],
    *,
    last_n: int = 20,
    apply: bool = True,
) -> dict[str, Any]:
    reflections = list_reflections(root, limit=last_n)
    taste = load_taste(root)
    before = json.loads(json.dumps(taste))

    # Aggregate from reflections
    defect_counter: Counter[str] = Counter()
    strength_bits: list[str] = []
    scores: list[float] = []
    rounds_list: list[int] = []

    for ref in reflections:
        if ref.get("winner_score") is not None:
            try:
                scores.append(float(ref["winner_score"]))
            except (TypeError, ValueError):
                pass
        if ref.get("rounds_used") is not None:
            try:
                rounds_list.append(int(ref["rounds_used"]))
            except (TypeError, ValueError):
                pass
        for d in (ref.get("taste_deltas") or {}).get("from_defects") or []:
            defect_counter[str(d)[:60]] += 1
            if is_soft_defect_phrase(str(d)):
                continue
            for h in _extract_hints(str(d), BAN_HINTS):
                if not is_soft_defect_phrase(h):
                    taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)
        for s in (ref.get("taste_deltas") or {}).get("from_strengths") or []:
            strength_bits.append(str(s)[:80])
            for h in _extract_hints(str(s), LIGHTING_HINTS + COMPOSITION_HINTS + TEMP_HINTS):
                if h in [x[1] for x in LIGHTING_HINTS]:
                    taste["preferred_lighting"] = _uniq_append(taste.get("preferred_lighting") or [], h)
                elif h in [x[1] for x in COMPOSITION_HINTS]:
                    taste["preferred_composition"] = _uniq_append(taste.get("preferred_composition") or [], h)
                elif h in [x[1] for x in TEMP_HINTS]:
                    taste["preferred_color_temperature"] = _uniq_append(taste.get("preferred_color_temperature") or [], h)

    # Scan recent redlines / recipes from memory entries
    entries = data.get("entries") or []
    recent_red = [e for e in entries if e.get("kind") == "style_redline"][-15:]
    for e in recent_red:
        summary = str(e.get("summary") or "")
        if is_soft_defect_phrase(summary):
            continue
        for h in _extract_hints(summary, BAN_HINTS):
            if not is_soft_defect_phrase(h):
                taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)
        if summary and len(summary) <= 50 and not is_soft_defect_phrase(summary):
            taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], summary)

    recent_rec = sorted(
        [e for e in entries if e.get("kind") == "recipe"],
        key=lambda e: rank_memory_entry(e),
        reverse=True,
    )[:10]
    recipe_strengthen: list[dict[str, str]] = []
    for e in recent_rec:
        summary = str(e.get("summary") or "")
        if summary:
            recipe_strengthen.append({
                "module": str(e.get("module") or ""),
                "id": str(e.get("id") or ""),
                "summary": summary[:100],
                "hint": "下次 warm-start 优先注入本条 recipe",
            })
            for h in _extract_hints(summary, LIGHTING_HINTS + COMPOSITION_HINTS):
                if h in [x[1] for x in LIGHTING_HINTS]:
                    taste["preferred_lighting"] = _uniq_append(taste.get("preferred_lighting") or [], h)
                else:
                    taste["preferred_composition"] = _uniq_append(taste.get("preferred_composition") or [], h)

    sc = taste.setdefault("signal_counts", {})
    sc["sessions"] = max(int(sc.get("sessions", 0)), len(reflections))

    top_defects = [{"text": t, "count": c} for t, c in defect_counter.most_common(8)]

    changes: list[str] = []
    for key in (
        "preferred_lighting",
        "preferred_composition",
        "preferred_line_weight",
        "preferred_color_temperature",
        "banned_habits",
        "style_notes",
    ):
        before_set = set(before.get(key) or [])
        after_list = taste.get(key) or []
        added = [x for x in after_list if x not in before_set]
        if added:
            changes.append(f"{key}: +{', '.join(added[-5:])}")

    # Strip soft junk before persist (defensive — covers prior polluted profiles)
    taste["banned_habits"] = [
        h for h in (taste.get("banned_habits") or []) if not is_soft_defect_phrase(str(h))
    ]

    if apply:
        save_taste(root, taste)
        # Write improve report sidecar
        report = {
            "ran_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
            "reflections_scanned": len(reflections),
            "avg_winner_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_rounds": round(sum(rounds_list) / len(rounds_list), 2) if rounds_list else None,
            "top_recurring_defects": top_defects,
            "recipe_strengthen": recipe_strengthen[:8],
            "taste_changes": changes,
            "taste_path": str(taste_path(root).relative_to(root)),
        }
        report_path = profile_dir(root) / "last_improve.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        report = {
            "ran_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
            "reflections_scanned": len(reflections),
            "avg_winner_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_rounds": round(sum(rounds_list) / len(rounds_list), 2) if rounds_list else None,
            "top_recurring_defects": top_defects,
            "recipe_strengthen": recipe_strengthen[:8],
            "taste_changes": changes,
            "dry_run": True,
        }

    return report


def cmd_improve(
    root: Path,
    data: dict[str, Any],
    action: str = "run",
    *,
    last_n: int = 20,
    apply: bool = True,
    silent: bool = False,
) -> int:
    if action in ("run", "reflect", ""):
        from .autopilot import compose_whisper_tip, print_whisper_tip, try_consume_tip_budget
        report = run_improve_pass(root, data, last_n=last_n, apply=apply)
        if silent:
            tip = compose_whisper_tip(
                taste_changes=list(report.get("taste_changes") or []),
                defects=(report.get("top_recurring_defects") or [{}])[0].get("text", "") if report.get("top_recurring_defects") else "",
            )
            if tip and try_consume_tip_budget(root, f"improve:{_now_cst().strftime('%Y%m%d%H')}"):
                print_whisper_tip(tip)
            return 0
        print("🧠 `/pmem-improve` 自我迭代完成" + ("（dry-run）" if not apply else "") + "（进阶 peek）")
        print(f"   · 扫描反思会话: {report.get('reflections_scanned')} 份（最近 {last_n}）")
        if report.get("avg_winner_score") is not None:
            print(f"   · 近期平均胜出分: {report['avg_winner_score']}")
        if report.get("avg_rounds") is not None:
            print(f"   · 近期平均收敛轮次: {report['avg_rounds']}")
        if report.get("top_recurring_defects"):
            print("   · 高频翻车点:")
            for d in report["top_recurring_defects"][:5]:
                print(f"      – ({d['count']}×) {d['text']}")
        if report.get("taste_changes"):
            print("   · 口味档案变聪明了:")
            for c in report["taste_changes"]:
                print(f"      + {c}")
        else:
            print("   · 口味档案：本次无新增短语（信号不足或已收敛）")
        if report.get("recipe_strengthen"):
            print("   · 强化优先 recipe（下次 warm-start 加权）:")
            for r in report["recipe_strengthen"][:5]:
                print(f"      · [{r.get('module')}] {r.get('summary')}")
        print(f"   · 档案路径: .memory-art/_profile/taste.json")
        print("   · 日常已静默自动驾驶；本命令为可选 peek。")
        return 0

    if action == "progress":
        return cmd_progress(root, data)

    print(f"未知 improve 子操作: {action}（run|progress）")
    return 1


def cmd_progress(root: Path, data: dict[str, Any], *, window_7: int = 7, window_30: int = 30) -> int:
    refs_all = list_reflections(root, limit=max(window_30, 50))
    taste = load_taste(root)

    def _stats(refs: list[dict[str, Any]]) -> dict[str, Any]:
        scores = []
        rounds = []
        for r in refs:
            try:
                if r.get("winner_score") is not None:
                    scores.append(float(r["winner_score"]))
            except (TypeError, ValueError):
                pass
            try:
                if r.get("rounds_used") is not None:
                    rounds.append(int(r["rounds_used"]))
            except (TypeError, ValueError):
                pass
        return {
            "n": len(refs),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_rounds": round(sum(rounds) / len(rounds), 2) if rounds else None,
            "pass_rate": round(
                sum(1 for r in refs if r.get("winner_passed")) / len(refs), 2
            ) if refs else None,
        }

    s7 = _stats(refs_all[:window_7])
    s30 = _stats(refs_all[:window_30])

    # Recurring redlines from entries
    red_counter: Counter[str] = Counter()
    for e in data.get("entries") or []:
        if e.get("kind") == "style_redline":
            red_counter[str(e.get("summary") or e.get("id") or "?")[:70]] += 1

    print("📈 pmem-art 个人进步曲线（基于真实会话反思；无会话时显示为空）\n")
    print(f"  最近 {window_7} 次会话:  n={s7['n']}  平均胜出分={s7['avg_score']}  平均轮次={s7['avg_rounds']}  达标率={s7['pass_rate']}")
    print(f"  最近 {window_30} 次会话: n={s30['n']}  平均胜出分={s30['avg_score']}  平均轮次={s30['avg_rounds']}  达标率={s30['pass_rate']}")
    print()
    sc = taste.get("signal_counts") or {}
    print(f"  口味信号: keeps={sc.get('keeps', 0)}  rejects={sc.get('rejects', 0)}  style_fixes={sc.get('style_fixes', 0)}  sessions={sc.get('sessions', 0)}")
    if taste.get("banned_habits"):
        print(f"  当前禁用习惯: {'；'.join((taste.get('banned_habits') or [])[-6:])}")
    if taste.get("preferred_lighting") or taste.get("preferred_composition"):
        bits = []
        if taste.get("preferred_lighting"):
            bits.append("光影=" + "/".join(taste["preferred_lighting"][-3:]))
        if taste.get("preferred_composition"):
            bits.append("构图=" + "/".join(taste["preferred_composition"][-3:]))
        print(f"  当前偏好: {'；'.join(bits)}")
    print()
    if red_counter:
        print("  高频红线（记忆库）:")
        for text, cnt in red_counter.most_common(5):
            print(f"    · ({cnt}×) {text}")
    else:
        print("  高频红线: （暂无）")

    # Capability metrics: weakness categories over newer vs older reflections
    cat_newer: Counter[str] = Counter()
    cat_older: Counter[str] = Counter()
    if len(refs_all) >= 2:
        mid = max(1, len(refs_all) // 2)
        for ref in refs_all[:mid]:
            blob = str(ref.get("what_still_weak") or "")
            for d in (ref.get("taste_deltas") or {}).get("from_defects") or []:
                blob += " " + str(d)
            for lesson in ref.get("lessons") or []:
                if isinstance(lesson, dict) and lesson.get("category") not in (None, "keep"):
                    cat_newer[str(lesson["category"])] += 1
            for c in classify_weakness(blob):
                cat_newer[c] += 1
        for ref in refs_all[mid:]:
            blob = str(ref.get("what_still_weak") or "")
            for d in (ref.get("taste_deltas") or {}).get("from_defects") or []:
                blob += " " + str(d)
            for lesson in ref.get("lessons") or []:
                if isinstance(lesson, dict) and lesson.get("category") not in (None, "keep"):
                    cat_older[str(lesson["category"])] += 1
            for c in classify_weakness(blob):
                cat_older[c] += 1
        print()
        print("  能力短板类别（新半程 vs 旧半程，下降=变强）:")
        allc = sorted(set(cat_newer) | set(cat_older), key=lambda c: -(cat_newer[c] + cat_older[c]))
        if not allc:
            print("    （暂无足够分类信号）")
        for c in allc[:8]:
            n, o = cat_newer[c], cat_older[c]
            arrow = "↓变强" if n < o else ("↑需练" if n > o else "→持平")
            print(f"    · {c}: 新={n} 旧={o}  {arrow}")

    # Knowledge breadth size
    try:
        from .knowledge import load_knowledge_index
        kidx = load_knowledge_index(root)
        print(f"\n  知识广度: {len(kidx.get('cards') or {})} 张卡片  (.memory-art/_knowledge/)")
    except Exception:
        pass

    print(f"\n  档案: .memory-art/_profile/taste.json  ·  反思: .memory-art/_reflections/")
    return 0


def cmd_taste(
    root: Path,
    data: dict[str, Any],
    action: str = "show",
    *,
    key: str = "",
    value: str = "",
) -> int:
    taste = load_taste(root)
    if action == "show":
        print("🎨 个人口味档案 (.memory-art/_profile/taste.json)\n")
        print(json.dumps(taste, ensure_ascii=False, indent=2))
        return 0
    if action == "update":
        allowed = {
            "preferred_lighting",
            "preferred_composition",
            "preferred_line_weight",
            "preferred_color_temperature",
            "banned_habits",
            "style_notes",
        }
        if key not in allowed:
            print(f"❌ key 须为: {', '.join(sorted(allowed))}")
            return 1
        if not value.strip():
            print("❌ 请传入 --value")
            return 1
        taste[key] = _uniq_append(list(taste.get(key) or []), value.strip())
        p = save_taste(root, taste)
        print(f"✅ 已更新 {key} += {value.strip()!r}")
        print(f"   → {p.relative_to(root)}")
        return 0
    print(f"未知 taste 子操作: {action}（show|update）")
    return 1

