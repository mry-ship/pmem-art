"""Warm-start pack: rank memory entries and build injection pack."""
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

from .project_library import ensure_project_library_bound, slugify_project_id
from .taste_profile import load_taste

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
) -> tuple[int, int, int, int, float, int, str]:
    """Simplest unified weighting key across all pmem-art recall points (Two-Layer Aware):
    (kind_priority, private_layer_priority, settled_priority, exact_module_match, round_score, query_token_overlap, date_str)
    settled_priority is 0 for provisional (未达阈值) recipes so they rank under confirmed entries.
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
    settled = 0 if str(e.get("status") or "active").lower() == "provisional" else 1
    return (kind_prio, private_prio, settled, exact_mod, extract_entry_score(e), overlap, date_str)


def build_warm_start_pack(
    root: Path,
    data: dict[str, Any],
    module: str,
    goal: str = "",
    top_n: int = 3,
) -> dict[str, Any]:
    """Assemble top recipes + redlines + personal taste for first-prompt injection."""
    entries = data.get("entries") or []
    modules = data.get("modules") or {}
    from lifecycle import MAX_INHERITS_DEPTH, resolve_module_lineage
    lineage = resolve_module_lineage(module, modules, max_depth=MAX_INHERITS_DEPTH, warn=False) if module else []
    parent = lineage[1] if len(lineage) > 1 else None
    lineage_set = set(lineage)

    def _mod_ok(em: str) -> bool:
        return (em in lineage_set) or (not module)

    def _entry_live(e: dict) -> bool:
        return str(e.get("status") or "active").lower() not in ("archived", "superseded", "inactive", "pending")

    from skills_kit.subject_lexicon import ui_shell_clone_task

    def _recipe_ok_for_shell_goal(e: dict) -> bool:
        if not ui_shell_clone_task(module=module, goal=goal):
            return True
        blob = f"{e.get('summary') or ''} {e.get('body') or ''}"
        if any(k in blob for k in ("奖励弹窗", "reward popup", "奖励面板")) and not any(
            k in blob
            for k in ("空内容", "空中心", "母版", "留白", "九宫格母版", "stretchable", "empty content")
        ):
            return False
        return True

    recipes = [
        e for e in entries
        if e.get("kind") == "recipe"
        and _mod_ok(e.get("module", ""))
        and _entry_live(e)
        and _recipe_ok_for_shell_goal(e)
    ]
    redlines = [
        e for e in entries
        if e.get("kind") == "style_redline" and _mod_ok(e.get("module", "")) and _entry_live(e)
    ]
    decisions = [
        e for e in entries
        if e.get("kind") == "art_decision" and _mod_ok(e.get("module", "")) and _entry_live(e)
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
    confirmed_recipes = [
        e for e in recipes
        if str(e.get("status") or "active").lower() != "provisional"
    ]
    if confirmed_recipes:
        conf += 0.45
        reasons.append(f"命中 {len(confirmed_recipes)} 条达标 recipe")
    elif recipes:
        reasons.append("只有未达标 provisional recipe，不计入定稿置信")
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
    if goal and confirmed_recipes:
        g_low = goal.lower()
        hit = sum(1 for e in confirmed_recipes if any(
            tok and tok in (e.get("summary") or "").lower()
            for tok in re.split(r"\s+|，|。|,", g_low) if len(tok) >= 2
        ))
        if hit:
            conf += 0.10
            reasons.append(f"目标与 recipe 关键词重叠 {hit}")

    # Two-layer knowledge recall: Project-Private (_knowledge) > Cross-Project Shared (~/.pmem-art/shared)
    from .knowledge import recall_layered_knowledge_cards
    recalled_cards = recall_layered_knowledge_cards(root, target_module=module, query=goal, limit=2)
    private_kcards = [c for c in recalled_cards if c.get("layer_scope") == "private"]
    shared_kcards = [c for c in recalled_cards if c.get("layer_scope") == "shared"]
    if shared_kcards or private_kcards:
        conf += 0.15
        reasons.append(f"挂载 {len(private_kcards)} 张项目知识卡 + {len(shared_kcards)} 张全局美术底层基础卡")

    conf = round(min(conf, 1.0), 2)
    fast_track_eligible = conf >= 0.70 and len(redlines) <= 5

    active_proj = ensure_project_library_bound(root)
    proj_id = active_proj.get("project_id") or slugify_project_id(root.name)
    proj_name = active_proj.get("project_name") or root.name
    prompt_block_lines = [
        "【Warm-Start 注入包 — 第 1 轮 Prompt 必须吸收】",
        f"- 所属专项记忆库: {proj_name} (.memory-art/projects/{proj_id}/)",
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

    # Knowledge cards already recalled above
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
        "project_id": proj_id,
        "project_name": proj_name,
        "active_project": active_proj,
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


WARM_START_MARK = "【Warm-Start 注入包"


def merge_warm_start_prompt(prompt: str, pack: dict[str, Any] | None) -> str:
    """Prepend the session warm-start block unless it is already in the prompt."""
    block = str((pack or {}).get("prompt_block") or "").strip()
    text = str(prompt or "").strip()
    if not block:
        return text
    if WARM_START_MARK in text or block in text:
        return text
    if not text:
        return block
    return f"{block}\n{text}"


def print_warm_start(pack: dict[str, Any]) -> None:
    print("🔥 Warm-Start 包已写入会话；`converge generate` 会自动并入提示词，不必手贴")
    print(f"   · 置信度: {pack.get('confidence', 0):.2f} | fast-track 资格: {'✅' if pack.get('fast_track_eligible') else '❌'}")
    for reason in pack.get("confidence_reasons") or []:
        print(f"   · {reason}")
    print()
    print(pack.get("prompt_block") or "")

