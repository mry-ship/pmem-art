#!/usr/bin/env python3
"""
pmem-art improve: 连续自我迭代 — warm-start + 会话反思 + 口味档案 + 进步曲线。

默认心智（静默自动驾驶 / Whisper Autopilot）：
  converge finish / 高信号 feedback → 后台自动写反思、更新 taste、强化 recipe/红线、
  悄悄 enqueue 1–2 条 learn 建议 → 最多吐出一行「小提示」。
  /pmem-improve · /pmem-coach · /pmem-learn · progress 为进阶 peek（--verbose 看全量）。
"""
from __future__ import annotations

import json
import os
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


def _now_cst() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


PROFILE_DIR = "_profile"
REFLECTIONS_DIR = "_reflections"
TASTE_FILE = "taste.json"

DEFAULT_TASTE: dict[str, Any] = {
    "version": 1,
    "updated_at": "",
    "preferred_lighting": [],
    "preferred_composition": [],
    "preferred_line_weight": [],
    "preferred_color_temperature": [],
    "banned_habits": [],
    "keep_phrases": [],
    "reject_phrases": [],
    "style_notes": [],
    "signal_counts": {
        "keeps": 0,
        "rejects": 0,
        "style_fixes": 0,
        "sessions": 0,
    },
}


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
    p = taste_path(root)
    if not p.is_file():
        taste = json.loads(json.dumps(DEFAULT_TASTE))
        taste["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
        return taste
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        data = {}
    out = json.loads(json.dumps(DEFAULT_TASTE))
    out.update({k: v for k, v in data.items() if k in out or k.startswith("_")})
    for k, v in DEFAULT_TASTE["signal_counts"].items():
        out.setdefault("signal_counts", {})
        out["signal_counts"].setdefault(k, v)
    return out


def save_taste(root: Path, taste: dict[str, Any]) -> Path:
    taste = dict(taste)
    taste["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    p = taste_path(root)
    p.write_text(json.dumps(taste, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
# Warm-start pack (inject into round-1 prompt before first generation)
# ---------------------------------------------------------------------------

def extract_entry_score(e: dict[str, Any]) -> float:
    for k in ("score", "winner_score"):
        if e.get(k) is not None:
            try:
                return float(e[k])
            except (TypeError, ValueError):
                pass
    ai_p = e.get("ai_params") or {}
    if isinstance(ai_p, dict) and ai_p.get("score") is not None:
        try:
            return float(ai_p["score"])
        except (TypeError, ValueError):
            pass
    blob = f"{e.get('summary') or ''} {e.get('body') or ''}"
    m = re.search(r"(\d+\.\d+)\s*(?:分|/\s*10)", blob)
    return float(m.group(1)) if m else 0.0


def rank_memory_entry(
    e: dict[str, Any],
    target_module: str = "",
    query: str = "",
    prioritize_kind: bool = False,
) -> tuple[int, int, int, float, int, str]:
    """Simplest unified weighting key across all pmem-art recall points (Two-Layer Aware):
    (kind_priority, private_layer_priority, exact_module_match, round_score, query_token_overlap, date_str)
    - private_layer_priority: 1 for project-private memories/cards (.memory-art/), 0 for cross-project shared (~/.pmem-art/shared/).
      Ensures project-private layer always ranks above shared layer when both match!
    Higher tuple sorts first with reverse=True.
    """
    q_tokens = [
        tok for tok in re.split(r"[\s,，。、·:：/|+()-]+", (query or "").lower())
        if len(tok) >= 2
    ]
    hay = " ".join([
        str(e.get("summary") or e.get("title") or ""),
        str(e.get("body") or ""),
        " ".join(str(x) for x in (e.get("tags") or e.get("aliases") or [])),
    ]).lower()
    overlap = sum(1 for tok in q_tokens if tok in hay)
    layer_scope = str(e.get("layer_scope") or e.get("layer_tier") or "private").lower()
    private_prio = 0 if layer_scope == "shared" else 1
    mod_val = str(e.get("module") or "")
    target_dom = target_module.split(".")[0] if "." in (target_module or "") else (target_module or "")
    tags_list = [str(x).lower() for x in (e.get("tags") or [])]
    exact_mod = 1 if (
        (target_module and mod_val == target_module)
        or (target_dom and target_dom.lower() in tags_list)
    ) else 0
    kind_prio = (10 - int(e.get("kind_order", 9))) if prioritize_kind else 0
    date_str = str(e.get("verified") or e.get("note_date") or e.get("updated_at") or e.get("id") or "")
    return (kind_prio, private_prio, exact_mod, extract_entry_score(e), overlap, date_str)


def build_warm_start_pack(
    root: Path,
    data: dict[str, Any],
    module: str,
    goal: str = "",
    top_n: int = 3,
) -> dict[str, Any]:
    """Assemble top recipes + redlines + personal taste for first-prompt injection."""
    entries = data.get("entries") or []
    parent = None
    modules = data.get("modules") or {}
    if module in modules:
        parent = modules[module].get("parent")
    if not parent and "." in module:
        cand = ".".join(module.split(".")[:-1])
        if cand in modules:
            parent = cand

    def _mod_ok(em: str) -> bool:
        return em in (module, parent) or (not module)

    recipes = [
        e for e in entries
        if e.get("kind") == "recipe" and _mod_ok(e.get("module", "")) and e.get("status", "active") != "archived"
    ]
    redlines = [
        e for e in entries
        if e.get("kind") == "style_redline" and _mod_ok(e.get("module", "")) and e.get("status", "active") != "archived"
    ]
    decisions = [
        e for e in entries
        if e.get("kind") == "art_decision" and _mod_ok(e.get("module", "")) and e.get("status", "active") != "archived"
    ]

    recipes = sorted(recipes, key=lambda e: rank_memory_entry(e, target_module=module, query=goal), reverse=True)[:top_n]
    redlines = sorted(redlines, key=lambda e: rank_memory_entry(e, target_module=module, query=goal), reverse=True)[: max(top_n + 2, 5)]
    decisions = sorted(decisions, key=lambda e: rank_memory_entry(e, target_module=module, query=goal), reverse=True)[:top_n]

    taste = load_taste(root)
    palette = (modules.get(module) or {}).get("palette") or []

    recipe_summaries = [
        {"id": e.get("id"), "summary": e.get("summary"), "module": e.get("module")}
        for e in recipes
    ]
    redline_summaries = [
        {"id": e.get("id"), "summary": e.get("summary"), "module": e.get("module")}
        for e in redlines
    ]

    # Confidence: strong recipe match + few redlines → fast-track eligible
    conf = 0.0
    reasons: list[str] = []
    if recipes:
        conf += 0.45
        reasons.append(f"命中 {len(recipes)} 条定稿 recipe")
    if decisions:
        conf += 0.15
        reasons.append(f"命中 {len(decisions)} 条审美拍板")
    if taste.get("preferred_lighting") or taste.get("preferred_composition"):
        conf += 0.15
        reasons.append("个人口味档案非空")
    if len(redlines) <= 3:
        conf += 0.15
        reasons.append(f"红线可控（{len(redlines)} 条）")
    elif len(redlines) <= 8:
        conf += 0.05
        reasons.append(f"红线中等（{len(redlines)} 条）")
    else:
        reasons.append(f"红线较多（{len(redlines)} 条）— 首轮需更谨慎")
    if goal and recipes:
        g_low = goal.lower()
        hit = sum(1 for e in recipes if any(
            tok and tok in (e.get("summary") or "").lower()
            for tok in re.split(r"\s+|，|。|,", g_low) if len(tok) >= 2
        ))
        if hit:
            conf += 0.10
            reasons.append(f"目标与 recipe 关键词重叠 {hit}")

    conf = round(min(conf, 1.0), 2)
    fast_track_eligible = conf >= 0.70 and len(redlines) <= 5

    prompt_block_lines = [
        "【Warm-Start 注入包 — 第 1 轮 Prompt 必须吸收】",
        f"- 目标模块: {module or '未指定'}",
        f"- 置信度: {conf:.2f}（fast-track 资格: {'是' if fast_track_eligible else '否'}）",
    ]
    if recipe_summaries:
        prompt_block_lines.append("- 优先复用定稿方向:")
        for r in recipe_summaries:
            prompt_block_lines.append(f"  · [{r.get('id')}] {r.get('summary')}")
    if redline_summaries:
        prompt_block_lines.append("- 必须避开红线:")
        for r in redline_summaries:
            prompt_block_lines.append(f"  · [{r.get('id')}] {r.get('summary')}")
    if decisions:
        prompt_block_lines.append("- 审美拍板:")
        for d in decisions[:top_n]:
            prompt_block_lines.append(f"  · {d.get('summary')}")
    if palette:
        prompt_block_lines.append(f"- 模块色板: {palette}")

    taste_bits = []
    for key, label in (
        ("preferred_lighting", "光影"),
        ("preferred_composition", "构图"),
        ("preferred_line_weight", "线宽"),
        ("preferred_color_temperature", "色温"),
    ):
        vals = taste.get(key) or []
        if vals:
            taste_bits.append(f"{label}={' / '.join(vals[-3:])}")
    banned = taste.get("banned_habits") or []
    if taste_bits:
        prompt_block_lines.append("- 个人口味: " + "；".join(taste_bits))
    if banned:
        prompt_block_lines.append("- 个人禁用习惯: " + "；".join(banned[-8:]))

    # Two-layer knowledge recall: Project-Private (_knowledge) > Cross-Project Shared (~/.pmem-art/shared)
    recalled_cards = recall_layered_knowledge_cards(root, target_module=module, query=goal, limit=4)
    private_kcards = [c for c in recalled_cards if c.get("layer_scope") == "private"]
    shared_kcards = [c for c in recalled_cards if c.get("layer_scope") == "shared"]
    if private_kcards:
        prompt_block_lines.append("- 项目私有知识卡 (Private Layer):")
        for c in private_kcards:
            prompt_block_lines.append(f"  · [{c.get('id')}] {c.get('title')}: {c.get('body')}")
    if shared_kcards:
        prompt_block_lines.append("- 跨项目共享通用技法卡 (Shared Layer · 无风格污染):")
        for c in shared_kcards:
            prompt_block_lines.append(f"  · [{c.get('id')}] {c.get('title')}: {c.get('body')}")

    prompt_block = "\n".join(prompt_block_lines)

    return {
        "module": module,
        "goal": goal,
        "confidence": conf,
        "fast_track_eligible": fast_track_eligible,
        "confidence_reasons": reasons,
        "top_recipes": recipe_summaries,
        "top_redlines": redline_summaries,
        "art_decisions": [{"id": e.get("id"), "summary": e.get("summary"), "layer_scope": "private"} for e in decisions],
        "private_knowledge": [{"id": c.get("id"), "title": c.get("title"), "body": c.get("body"), "layer_scope": "private"} for c in private_kcards],
        "shared_knowledge": [{"id": c.get("id"), "title": c.get("title"), "body": c.get("body"), "layer_scope": "shared"} for c in shared_kcards],
        "palette": palette,
        "taste_snapshot": {
            "preferred_lighting": taste.get("preferred_lighting", [])[-5:],
            "preferred_composition": taste.get("preferred_composition", [])[-5:],
            "preferred_line_weight": taste.get("preferred_line_weight", [])[-5:],
            "preferred_color_temperature": taste.get("preferred_color_temperature", [])[-5:],
            "banned_habits": taste.get("banned_habits", [])[-10:],
        },
        "prompt_block": prompt_block,
        "built_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
    }


def print_warm_start(pack: dict[str, Any]) -> None:
    print("🔥 Warm-Start 包已注入收敛会话（第 1 轮 Prompt 请完整吸收）")
    print(f"   · 置信度: {pack.get('confidence', 0):.2f} | fast-track 资格: {'✅' if pack.get('fast_track_eligible') else '❌'}")
    for reason in pack.get("confidence_reasons") or []:
        print(f"   · {reason}")
    print()
    print(pack.get("prompt_block") or "")


# ---------------------------------------------------------------------------
# Session reflection (after converge finish --apply)
# ---------------------------------------------------------------------------

def write_session_reflection(
    root: Path,
    sess: dict[str, Any],
    *,
    winner: dict[str, Any] | None = None,
    outcome: str = "",
) -> Path:
    winner = winner or sess.get("winner") or {}
    rounds = sess.get("rounds") or []
    stamp = _now_cst().strftime("%Y%m%d_%H%M%S")
    sid = sess.get("session_id") or "latest"
    path = reflections_dir(root) / f"{stamp}_{sid}.json"

    passed = [r for r in rounds if r.get("passed")]
    failed = [r for r in rounds if not r.get("passed")]
    fixed = [r.get("next_fix") for r in failed if r.get("next_fix")]
    still_weak = winner.get("defects") if winner and not winner.get("passed") else ""
    if winner and winner.get("passed"):
        still_weak = "无明显硬伤（已达标）" if not (winner.get("defects") or "").strip() else f"残余可接受点：{winner.get('defects')}"

    taste_deltas: dict[str, list[str]] = {
        "from_strengths": [],
        "from_defects": [],
    }
    if winner.get("strengths"):
        taste_deltas["from_strengths"].append(str(winner["strengths"])[:120])
    for r in failed[-3:]:
        if r.get("defects"):
            taste_deltas["from_defects"].append(str(r["defects"])[:100])

    reflection = {
        "schema": "pmem-art.reflection.v1",
        "written_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
        "session_id": sid,
        "goal": sess.get("goal"),
        "module": sess.get("module"),
        "converge_mode": sess.get("converge_mode") or sess.get("quality_mode") or "quality",
        "guided_mode": sess.get("mode"),
        "threshold": sess.get("threshold", 9.5),
        "max_rounds": sess.get("max_rounds", 8),
        "rounds_used": len(rounds),
        "winner_round": winner.get("round"),
        "winner_score": winner.get("score"),
        "winner_image": winner.get("image"),
        "winner_passed": bool(winner.get("passed")),
        "outcome": outcome,
        "what_fixed": fixed[-6:],
        "what_still_weak": still_weak,
        "strengths": winner.get("strengths"),
        "taste_deltas": taste_deltas,
        "warm_start_confidence": (sess.get("warm_start") or {}).get("confidence"),
        "fast_track": bool(sess.get("fast_track")),
        "scores": [{"round": r.get("round"), "score": r.get("score"), "passed": r.get("passed")} for r in rounds],
    }
    path.write_text(json.dumps(reflection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def list_reflections(root: Path, limit: int = 30) -> list[dict[str, Any]]:
    d = reflections_dir(root)
    files = sorted(d.glob("*.json"), key=lambda p: p.name, reverse=True)[:limit]
    out: list[dict[str, Any]] = []
    for f in files:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


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
        taste["keep_phrases"] = _uniq_append(taste.get("keep_phrases") or [], t[:80])
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
        taste["reject_phrases"] = _uniq_append(taste.get("reject_phrases") or [], t[:80])
        for h in _extract_hints(t, BAN_HINTS):
            taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)
        # raw short reject also becomes banned habit
        if len(t) <= 40:
            taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], t)
    elif kind in ("visual_correction", "art_decision"):
        sc["style_fixes"] = int(sc.get("style_fixes", 0)) + 1
        taste["style_notes"] = _uniq_append(taste.get("style_notes") or [], t[:100])
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
            taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)

    save_taste(root, taste)
    return taste


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
            for h in _extract_hints(str(d), BAN_HINTS):
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
        for h in _extract_hints(summary, BAN_HINTS):
            taste["banned_habits"] = _uniq_append(taste.get("banned_habits") or [], h)
        if summary and len(summary) <= 50:
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
    blob = f"{defects}\n{next_fix}\n{strengths}\n{dims}"
    cats = classify_weakness(blob)
    if not cats and defects:
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


# ---------------------------------------------------------------------------
# Knowledge atlas — auto-expand breadth
# ---------------------------------------------------------------------------

KNOWLEDGE_DIR = "_knowledge"

DOMAIN_SEED_CARDS: dict[str, list[dict[str, str]]] = {
    "character": [
        {"id": "anatomy-head-ratio", "title": "头身比尺规", "tags": ["anatomy", "character"], "body": "立绘常用 7~8 头身；Q版 2~3 头身。草图阶段先标刻度。"},
        {"id": "eye-hierarchy", "title": "五官主次", "tags": ["anatomy", "character"], "body": "先定眼位与眉弓，再嘴鼻；义眼/异色瞳要作为识别锚点锁定。"},
    ],
    "scene": [
        {"id": "atmospheric-perspective", "title": "大气透视", "tags": ["scene", "lighting"], "body": "远景降对比降饱和，近景保持边缘清晰，增强纵深。"},
        {"id": "golden-hour-scene", "title": "黄金时刻场景光", "tags": ["scene", "lighting"], "body": "低角度暖光 + 长影；避开正午顶光死白。"},
    ],
    "ui": [
        {"id": "nine-slice-basics", "title": "九宫格基础", "tags": ["ui", "ui_9slice"], "body": "四角固定、四边单向、中心双向；中心区禁止复杂花纹。"},
        {"id": "button-state-family", "title": "按钮状态族", "tags": ["ui"], "body": "normal/hover/pressed/disabled 同外形同色板，只改明度与内阴影。"},
    ],
    "vfx": [
        {"id": "readability-silhouette", "title": "特效可读剪影", "tags": ["vfx"], "body": "序列帧每帧剪影可辨；主色不超过 2，高光一条即可。"},
    ],
    "anim": [
        {"id": "key-extreme-breakdown", "title": "关键帧-极端帧-中分帧", "tags": ["anim"], "body": "先定 key 与 extreme，再补 breakdown；避免平均插值发僵。"},
    ],
    "brand": [
        {"id": "palette-70-20-10", "title": "色板 70/20/10", "tags": ["brand", "color_palette"], "body": "主色70%、辅色20%、点缀10%；点缀勿抢主体。"},
    ],
}

ADJACENT_BREADTH: dict[str, list[str]] = {
    "character": ["scene", "lighting", "narrative_camera"],
    "scene": ["lighting", "narrative_camera", "brand"],
    "ui": ["icon_consistency", "brand", "color_palette"],
    "vfx": ["anim", "lighting"],
    "anim": ["vfx", "anatomy"],
    "brand": ["color_palette", "style_lock"],
    "misc": ["brand", "lighting"],
}


# Style-specific or project-bound patterns that MUST NOT enter the cross-project shared layer
STYLE_SPECIFIC_PATTERNS: list[str] = [
    r"#[0-9a-fA-F]{3,8}\b",
    r"青瓷|玄青|鎏金|赛博霓虹|霓虹紫|水彩|赛璐珞|厚涂|像素风|watercolor|cel[-\s]?shad|painterly|pixel[-\s]?art",
    r"阿斯特拉|Astra|莱拉|Lyra|云海星穹",
]


def is_style_agnostic_universal_card(card: dict[str, Any]) -> tuple[bool, str]:
    """Verify whether a knowledge card is universally useful and style-agnostic
    (e.g., head-to-body ratio, 70-20-10 color proportion law, atmospheric perspective,
    9-slice structure, silhouette readability) rather than bound to a specific project's
    art style, palette HEX, or character setting.
    """
    cid = str(card.get("id") or "").lower()
    kind = str(card.get("kind") or "").lower()
    tags = [str(t).lower() for t in (card.get("tags") or [])]
    blob = f"{card.get('title') or ''} {card.get('body') or ''}"

    if kind == "style_fork" or cid.startswith("style-") or "style" in tags or "style_lock" in tags:
        return False, "包含特定画风/风格锁定标签 (style / style_lock / style_fork)，仅限项目私有层"
    if cid in ("tech-watercolor", "tech-celshade", "tech-painterly", "tech-pixel"):
        return False, "属于特定渲染画风技法，仅保留在项目私有层以防跨项目串风"
    for pat in STYLE_SPECIFIC_PATTERNS:
        m = re.search(pat, blob, re.I)
        if m:
            return False, f"包含项目专属色值/画风/角色词 ({m.group(0)})，禁止上浮至跨项目共享层"
    return True, "通用无风格绑定美术规律（可跨项目共享）"


def shared_knowledge_dir(root: Path | None = None) -> Path:
    """Global cross-project shared layer directory (~/.pmem-art/shared/ by default,
    or overridden by PMEM_ART_SHARED_DIR environment variable).
    """
    env_dir = os.environ.get("PMEM_ART_SHARED_DIR", "").strip()
    if env_dir:
        d = Path(env_dir).expanduser().resolve()
    else:
        d = (Path.home() / ".pmem-art" / "shared").resolve()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _shared_knowledge_index_path(root: Path | None = None) -> Path:
    return shared_knowledge_dir(root) / "index.json"


def load_shared_knowledge_index(root: Path | None = None, *, auto_seed: bool = True) -> dict[str, Any]:
    p = _shared_knowledge_index_path(root)
    if not p.is_file():
        if auto_seed:
            return ensure_shared_knowledge_seeded(root)
        return {"version": 1, "layer_scope": "shared", "cards": {}, "updated_at": ""}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if auto_seed and not (data.get("cards") or {}):
            return ensure_shared_knowledge_seeded(root)
        return data
    except Exception:
        return {"version": 1, "layer_scope": "shared", "cards": {}, "updated_at": ""}


def save_shared_knowledge_index(idx: dict[str, Any], root: Path | None = None) -> Path:
    idx["layer_scope"] = "shared"
    idx["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    p = _shared_knowledge_index_path(root)
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def upsert_shared_knowledge_card(
    *,
    card_id: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    source: str = "shared_seed",
    promoted_from: str = "",
    root: Path | None = None,
    force: bool = False,
) -> tuple[bool, str, Path | None]:
    candidate = {
        "id": card_id,
        "title": title,
        "body": body,
        "tags": tags or [],
    }
    ok, reason = is_style_agnostic_universal_card(candidate)
    if not ok and not force:
        return False, reason, None

    idx = load_shared_knowledge_index(root, auto_seed=False)
    cards = idx.setdefault("cards", {})
    card = {
        "id": card_id,
        "title": title,
        "body": body,
        "tags": tags or [],
        "source": source,
        "layer_scope": "shared",
        "universal": True,
        "promoted_from": promoted_from,
        "updated_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
    }
    cards[card_id] = card
    safe = re.sub(r"[^\w\-.]+", "_", card_id)[:80]
    md = shared_knowledge_dir(root) / f"{safe}.md"
    md.write_text(
        f"---\nid: {card_id}\ntitle: {json.dumps(title, ensure_ascii=False)}\n"
        f"layer_scope: shared\nuniversal: true\n"
        f"tags: {json.dumps(tags or [], ensure_ascii=False)}\nsource: {source}\n---\n\n"
        f"# {title}\n\n{body.strip()}\n",
        encoding="utf-8",
    )
    save_shared_knowledge_index(idx, root)
    return True, reason, md


def ensure_shared_knowledge_seeded(root: Path | None = None) -> dict[str, Any]:
    """Ensure the global cross-project shared store (~/.pmem-art/shared/) has the
    universal style-agnostic seed cards (head-to-body ratio, 70-20-10 law, perspective,
    9-slice, silhouette readability, etc.).
    """
    idx = {"version": 1, "layer_scope": "shared", "cards": {}, "updated_at": ""}
    p = _shared_knowledge_index_path(root)
    if p.is_file():
        try:
            idx = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            pass
    cards = idx.setdefault("cards", {})
    changed = False
    for dom, card_list in DOMAIN_SEED_CARDS.items():
        for c in card_list:
            cid = c["id"]
            if cid not in cards:
                ok, _ = is_style_agnostic_universal_card(c)
                if ok:
                    cards[cid] = {
                        "id": cid,
                        "title": c["title"],
                        "body": c["body"],
                        "tags": list(c.get("tags") or []),
                        "source": "shared_seed",
                        "layer_scope": "shared",
                        "universal": True,
                        "promoted_from": "builtin_universal_seed",
                        "updated_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
                    }
                    safe = re.sub(r"[^\w\-.]+", "_", cid)[:80]
                    md = shared_knowledge_dir(root) / f"{safe}.md"
                    if not md.exists():
                        md.write_text(
                            f"---\nid: {cid}\ntitle: {json.dumps(c['title'], ensure_ascii=False)}\n"
                            f"layer_scope: shared\nuniversal: true\n"
                            f"tags: {json.dumps(c.get('tags') or [], ensure_ascii=False)}\nsource: shared_seed\n---\n\n"
                            f"# {c['title']}\n\n{c['body'].strip()}\n",
                            encoding="utf-8",
                        )
                    changed = True
    if changed or not p.is_file():
        save_shared_knowledge_index(idx, root)
    return idx


def recall_layered_knowledge_cards(
    root: Path,
    target_module: str = "",
    query: str = "",
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Recall knowledge cards across BOTH layers (Project-Private .memory-art/_knowledge/
    and Cross-Project Shared ~/.pmem-art/shared/), ranked by `rank_memory_entry` so
    project-private cards always rank above shared cards when both match.
    """
    priv_idx = load_knowledge_index(root)
    priv_cards = list((priv_idx.get("cards") or {}).values())
    shared_idx = load_shared_knowledge_index(root, auto_seed=True)
    shared_cards = list((shared_idx.get("cards") or {}).values())

    target_dom = target_module.split(".")[0].lower() if "." in (target_module or "") else (target_module or "").lower()
    domain_adj = set(ADJACENT_BREADTH.get(target_dom, [])) | ({target_dom} if target_dom else set())

    candidates: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    # 1. Project-private cards first (tagged layer_scope='private')
    for c in priv_cards:
        c_copy = dict(c)
        c_copy["layer_scope"] = "private"
        cid = str(c_copy.get("id") or "")
        if cid:
            seen_ids.add(cid)
        candidates.append(c_copy)

    # 2. Cross-project shared cards (tagged layer_scope='shared', skipped if overridden privately)
    for c in shared_cards:
        cid = str(c.get("id") or "")
        if cid in seen_ids:
            continue
        c_copy = dict(c)
        c_copy["layer_scope"] = "shared"
        candidates.append(c_copy)

    # Filter to cards relevant to target_module/domain or query when module is specified
    filtered: list[dict[str, Any]] = []
    for c in candidates:
        tags = {str(t).lower() for t in (c.get("tags") or [])}
        if not target_dom or (tags & domain_adj) or ("brand" in tags) or ("color_palette" in tags):
            filtered.append(c)
        elif query and rank_memory_entry(c, target_module=target_module, query=query)[4] > 0:
            filtered.append(c)

    filtered.sort(
        key=lambda c: rank_memory_entry(c, target_module=target_module, query=query),
        reverse=True,
    )
    return filtered[:limit]


def promote_card_to_shared(
    root: Path,
    card_id: str,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Promote a project-private knowledge card to the cross-project shared layer
    if it is style-agnostic and universally applicable.
    """
    priv_idx = load_knowledge_index(root)
    priv_cards = priv_idx.get("cards") or {}
    if card_id not in priv_cards:
        return {"ok": False, "id": card_id, "reason": f"项目私有知识库中不存在卡片 {card_id}"}
    card = priv_cards[card_id]
    ok, reason, md_path = upsert_shared_knowledge_card(
        card_id=card["id"],
        title=card.get("title") or card["id"],
        body=card.get("body") or "",
        tags=list(card.get("tags") or []),
        source="promoted_from_project",
        promoted_from=root.name,
        root=root,
        force=force,
    )
    if ok:
        card["promoted_to_shared"] = True
        save_knowledge_index(root, priv_idx)
    return {
        "ok": ok,
        "id": card_id,
        "title": card.get("title"),
        "reason": reason,
        "shared_path": str(md_path) if md_path else "",
    }


def knowledge_dir(root: Path) -> Path:
    d = _mem_root(root) / KNOWLEDGE_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def _knowledge_index_path(root: Path) -> Path:
    return knowledge_dir(root) / "index.json"


def load_knowledge_index(root: Path) -> dict[str, Any]:
    p = _knowledge_index_path(root)
    if not p.is_file():
        return {"version": 1, "layer_scope": "private", "cards": {}, "updated_at": ""}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("layer_scope", "private")
        for c in (data.get("cards") or {}).values():
            if isinstance(c, dict):
                c.setdefault("layer_scope", "private")
        return data
    except Exception:
        return {"version": 1, "layer_scope": "private", "cards": {}, "updated_at": ""}


def save_knowledge_index(root: Path, idx: dict[str, Any]) -> Path:
    idx["layer_scope"] = "private"
    idx["updated_at"] = _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8")
    p = _knowledge_index_path(root)
    p.write_text(json.dumps(idx, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return p


def upsert_knowledge_card(
    root: Path,
    *,
    card_id: str,
    title: str,
    body: str,
    tags: list[str] | None = None,
    source: str = "auto",
    promote_if_universal: bool = True,
) -> Path:
    idx = load_knowledge_index(root)
    cards = idx.setdefault("cards", {})
    candidate = {"id": card_id, "title": title, "body": body, "tags": tags or []}
    is_univ, _ = is_style_agnostic_universal_card(candidate)
    card = {
        "id": card_id,
        "title": title,
        "body": body,
        "tags": tags or [],
        "source": source,
        "layer_scope": "private",
        "universal": is_univ,
        "promoted_to_shared": False,
        "updated_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
    }
    if promote_if_universal and is_univ:
        ok, _, _ = upsert_shared_knowledge_card(
            card_id=card_id,
            title=title,
            body=body,
            tags=tags or [],
            source=f"auto_promoted:{source}",
            promoted_from=root.name,
            root=root,
        )
        card["promoted_to_shared"] = ok

    cards[card_id] = card
    # also write individual markdown for human browsing
    safe = re.sub(r"[^\w\-.]+", "_", card_id)[:80]
    md = knowledge_dir(root) / f"{safe}.md"
    md.write_text(
        f"---\nid: {card_id}\ntitle: {json.dumps(title, ensure_ascii=False)}\n"
        f"layer_scope: private\nuniversal: {str(is_univ).lower()}\n"
        f"tags: {json.dumps(tags or [], ensure_ascii=False)}\nsource: {source}\n---\n\n"
        f"# {title}\n\n{body.strip()}\n",
        encoding="utf-8",
    )
    save_knowledge_index(root, idx)
    return md


def ingest_term_to_knowledge(root: Path, text: str, *, source: str = "feedback") -> list[str]:
    """When feedback/ref-analysis introduces technique/style terms, grow atlas."""
    created: list[str] = []
    term_map = [
        (r"水彩|watercolor", "tech-watercolor", "水彩渲染", ["style", "material"], "边缘扩散、纸本纹理、低饱和层染；避免厚涂油腻高光。"),
        (r"赛璐珞|cel[\s-]?shad", "tech-celshade", "赛璐珞分层", ["style", "material"], "硬边色块分层，高光形状干净，层数克制。"),
        (r"厚涂|painterly|oil", "tech-painterly", "厚涂笔触", ["style", "material"], "可见笔触方向跟随形体，暗部透气勿脏。"),
        (r"像素|pixel", "tech-pixel", "像素艺术", ["style"], "锁调色板与像素网格，禁止糊边抗锯齿乱入。"),
        (r"九宫格|9[- ]?slice", "tech-9slice", "九宫格切图", ["ui"], "四角固定、中心可拉伸；中心禁止复杂装饰。"),
        (r"侧逆光|rim\s*light", "light-rim", "侧逆光", ["lighting"], "轮廓分离主体与背景，高光条沿边缘走。"),
        (r"黄金时刻|golden\s*hour", "light-golden-hour", "黄金时刻光", ["lighting", "scene"], "低角度暖光与长影，适合 Key Art。"),
        (r"大气透视|atmospheric", "scene-atm-persp", "大气透视", ["scene"], "远景降对比，近景保边缘。"),
        (r"Q版|chibi", "style-chibi", "Q版头身", ["character", "style"], "2~3 头身，五官放大但识别锚点保留。"),
        (r"电影感|cinematic", "cam-cinematic", "电影感镜头", ["narrative_camera"], "景深、侧逆光、叙事构图优先于装饰细节。"),
        (r"currentColor|stroke-width|viewBox", "icon-svg-spec", "SVG 图标规格", ["icon_consistency", "ui"], "统一 viewBox / stroke / currentColor，视觉重量一致。"),
    ]
    for pat, cid, title, tags, body in term_map:
        if re.search(pat, text or "", re.I):
            idx = load_knowledge_index(root)
            if cid not in (idx.get("cards") or {}):
                upsert_knowledge_card(root, card_id=cid, title=title, body=body, tags=tags, source=source)
                created.append(cid)
            else:
                # refresh touch
                upsert_knowledge_card(root, card_id=cid, title=title, body=body, tags=tags, source=source)
                created.append(cid)
    return list(dict.fromkeys(created))


def propose_breadth_expansions(
    root: Path,
    data: dict[str, Any],
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Suggest 3–5 breadth expansions based on active domains vs gaps."""
    modules = data.get("modules") or {}
    active_domains: set[str] = set()
    for mid, cfg in modules.items():
        if (cfg or {}).get("status", "active") != "active":
            continue
        active_domains.add(mid.split(".")[0] if "." in mid else mid)

    idx = load_knowledge_index(root)
    have = set((idx.get("cards") or {}).keys())
    proposals: list[dict[str, Any]] = []

    # Seed cards missing for active domains
    for dom in sorted(active_domains):
        for card in DOMAIN_SEED_CARDS.get(dom, []):
            if card["id"] not in have:
                proposals.append({
                    "kind": "knowledge_card",
                    "id": card["id"],
                    "title": card["title"],
                    "tags": card.get("tags") or [],
                    "body": card.get("body") or "",
                    "reason": f"你已有 {dom} 域模块，但知识库缺少「{card['title']}」",
                    "optional_module_stub": "",
                })

    # Adjacent domain gaps
    for dom in sorted(active_domains):
        for adj in ADJACENT_BREADTH.get(dom, []):
            # adj may be category not domain
            if adj in DOMAIN_SEED_CARDS and adj not in active_domains:
                for card in DOMAIN_SEED_CARDS[adj][:1]:
                    if card["id"] not in have:
                        proposals.append({
                            "kind": "adjacent_domain",
                            "id": card["id"],
                            "title": card["title"],
                            "tags": card.get("tags") or [],
                            "body": card.get("body") or "",
                            "reason": f"从 {dom} 扩展到相邻域 {adj}：补「{card['title']}」",
                            "optional_module_stub": f"{adj}.General",
                        })
            # category-level knowledge
            if adj in DRILLS and f"cap-{adj}" not in have:
                proposals.append({
                    "kind": "capability_card",
                    "id": f"cap-{adj}",
                    "title": f"能力卡：{adj}",
                    "tags": [adj, "capability"],
                    "body": DRILLS[adj][0],
                    "reason": f"短板/相邻能力「{adj}」尚无知识卡",
                    "optional_module_stub": "",
                })

    # Style fork suggestions from taste banned/preferred
    taste = load_taste(root)
    if taste.get("banned_habits") and "style-anti-neon" not in have:
        proposals.append({
            "kind": "style_fork",
            "id": "style-anti-neon",
            "title": "反霓虹风格约束",
            "tags": ["style_lock", "brand"],
            "body": "禁用霓虹紫与廉价赛博高光；主色走青瓷白/墨蓝/鎏金或项目色板。",
            "reason": "口味档案含霓虹/赛博类禁用 → 固化为风格知识卡",
            "optional_module_stub": "",
        })

    # de-dupe by id
    seen: set[str] = set()
    uniq: list[dict[str, Any]] = []
    for p in proposals:
        if p["id"] in seen:
            continue
        seen.add(p["id"])
        uniq.append(p)
        if len(uniq) >= limit:
            break
    return uniq


def accept_breadth_proposals(
    root: Path,
    data: dict[str, Any],
    proposals: list[dict[str, Any]],
    *,
    seed_modules: bool = False,
) -> dict[str, Any]:
    written: list[str] = []
    stubs: list[str] = []
    for p in proposals:
        path = upsert_knowledge_card(
            root,
            card_id=p["id"],
            title=p["title"],
            body=p.get("body") or p.get("reason") or "",
            tags=list(p.get("tags") or []),
            source="learn_accept",
        )
        written.append(str(path.relative_to(root)))
        stub = p.get("optional_module_stub") or ""
        if seed_modules and stub:
            # write empty scaffold entry note only — do not mutate modules.yaml aggressively
            mod_dir = _mem_root(root) / "entries" / stub
            mod_dir.mkdir(parents=True, exist_ok=True)
            note = mod_dir / "LEARN_SEED.md"
            if not note.exists():
                note.write_text(
                    f"---\nid: LEARNSEED\nmodule: {stub}\nkind: art_plan\nstatus: active\n"
                    f"summary: \"知识广度扩展种子模块\"\n---\n\n"
                    f"由 `/pmem-learn` 接受建议创建的空种子。可用 `accept` / `ingest` 正式激活。\n"
                    f"关联知识卡: {p['id']} — {p['title']}\n",
                    encoding="utf-8",
                )
                stubs.append(stub)
    return {"written": written, "module_stubs": stubs}


def cmd_learn(
    root: Path,
    data: dict[str, Any],
    action: str = "suggest",
    *,
    limit: int = 5,
    accept_all: bool = False,
    seed_modules: bool = False,
    ids: list[str] | None = None,
    silent: bool = False,
) -> int:
    if action in ("suggest", "propose", ""):
        props = propose_breadth_expansions(root, data, limit=limit)
        stash = profile_dir(root) / "learn_proposals.json"
        stash.write_text(json.dumps({"proposals": props, "at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"), "silent": silent}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if silent:
            return 0
        print("🌍 `/pmem-learn` 知识广度扩展建议（进阶 peek）\n")
        if not props:
            print("   · 暂无新建议（知识库已较完整，或模块仍空）。日常已在 finish 后静默 enqueue。")
            return 0
        for i, p in enumerate(props, 1):
            print(f"   {i}. [{p.get('kind')}] {p.get('title')}  ({p.get('id')})")
            print(f"      原因: {p.get('reason')}")
            if p.get("optional_module_stub"):
                print(f"      可选模块种子: {p['optional_module_stub']}")
        print(f"\n   · 建议已暂存: .memory-art/_profile/learn_proposals.json")
        print("   · 接受全部: python3 pmem_art.py learn accept --all")
        print("   · 接受指定: python3 pmem_art.py learn accept --ids id1,id2")
        if accept_all:
            return cmd_learn(root, data, "accept", accept_all=True, seed_modules=seed_modules, limit=limit, silent=False)
        return 0

    if action == "accept":
        stash = profile_dir(root) / "learn_proposals.json"
        props: list[dict[str, Any]] = []
        if stash.is_file():
            try:
                props = (json.loads(stash.read_text(encoding="utf-8")).get("proposals")) or []
            except Exception:
                props = []
        if not props:
            props = propose_breadth_expansions(root, data, limit=limit)
        if ids:
            idset = set(ids)
            props = [p for p in props if p.get("id") in idset]
        elif not accept_all:
            print("❌ 请指定 --all 或 --ids id1,id2")
            return 1
        result = accept_breadth_proposals(root, data, props, seed_modules=seed_modules)
        print("✅ 已写入知识卡:")
        for w in result["written"]:
            print(f"   · {w}")
        if result["module_stubs"]:
            print("🌱 模块种子:")
            for s in result["module_stubs"]:
                print(f"   · {s}")
        return 0

    if action == "list":
        idx = load_knowledge_index(root)
        priv_cards = idx.get("cards") or {}
        s_idx = load_shared_knowledge_index(root, auto_seed=True)
        shared_cards = s_idx.get("cards") or {}
        print(f"📚 双层知识广度图谱（项目私有 {len(priv_cards)} 张 + 跨项目全局共享 {len(shared_cards)} 张）\n")
        print(f"🔒 [Layer 1 · 项目私有层] .memory-art/_knowledge/ ({len(priv_cards)} 张):")
        if not priv_cards:
            print("   （当前项目私有层为空）")
        for cid, c in sorted(priv_cards.items()):
            prom = " 🌐[已同步共享层]" if c.get("promoted_to_shared") else " 🔒[仅本项目]"
            print(f"   · {cid}: {c.get('title')}  tags={c.get('tags')}{prom}")
        print(f"\n🌐 [Layer 2 · 跨项目共享层] {shared_knowledge_dir(root)} ({len(shared_cards)} 张 · 纯通用无风格绑定):")
        for cid, c in sorted(shared_cards.items()):
            print(f"   · {cid}: {c.get('title')}  tags={c.get('tags')}  (from={c.get('promoted_from') or 'seed'})")
        return 0

    if action == "promote":
        priv_idx = load_knowledge_index(root)
        priv_cards = priv_idx.get("cards") or {}
        target_ids = ids if ids else (list(priv_cards.keys()) if accept_all else [])
        if not target_ids:
            print("❌ 请指定 --ids card1,card2 或 --all 将项目私有通用知识卡上浮至跨项目共享层")
            return 1
        promoted, blocked = [], []
        for cid in target_ids:
            res = promote_card_to_shared(root, cid, force=False)
            if res.get("ok"):
                promoted.append(res)
            else:
                blocked.append(res)
        if promoted:
            print(f"🌐 已上浮至跨项目共享层 ({shared_knowledge_dir(root)}):")
            for r in promoted:
                print(f"   ✅ {r['id']} ({r.get('title')}) — {r.get('reason')}")
        if blocked:
            print("🔒 以下卡片因含项目特定画风/色板被拦截在项目私有层（防止跨项目污染）:")
            for r in blocked:
                print(f"   🛡️ {r['id']} ({r.get('title', '')}) — {r.get('reason')}")
        return 0

    print(f"未知 learn 子操作: {action}（suggest|accept|list|promote）")
    return 1
