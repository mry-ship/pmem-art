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
# Injection guardrails: stop cross-domain taste/recipe bleed into prompts
# ---------------------------------------------------------------------------

# Strong topic tags: if an entry/habit carries one the current task lacks, drop it.
_TOPIC_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("xmas", re.compile(r"圣诞|christmas|xmas|ginger|gingerbread|暴雪呵气|冰晶碎玻璃", re.I)),
    ("candy_merge", re.compile(r"糖果|焊蛋糕|气球档|棒糖|马戏|奖牌体量|L1像素锁|L1锁与气球|节日合成", re.I)),
    ("merge_ladder", re.compile(
        r"合成梯|五链合成|整表多格|邻档剪影|同域合理升级|shop_ladder|"
        r"白底不可接受|禁止换物种|零件必须累计|档差要一眼|和L1一样透明|黑空底",
        re.I,
    )),
    ("softcandy", re.compile(r"草莓软糖|软糖SSS|籽粒凹|蒂叶|半透明SSS|软糖表面", re.I)),
    ("instrument", re.compile(r"乐器|竖琴|钢琴|species_change|吉他同物件", re.I)),
    ("building", re.compile(r"建筑|木屋|城堡|evermerge|庄园|吊桥|洋葱圆顶|木棚", re.I)),
    ("bird_merge", re.compile(r"鸟合成|禽类|母鸡|birds?merge|无脸抠|鸡群|翅层|尾扇", re.I)),
    ("ui_shell", re.compile(r"主菜单|HUD|九宫格|顶栏|底栏|米黄纸板|Clash底栏|设置同排|侧栏|资源栏", re.I)),
    ("app_icon", re.compile(r"App Icon|1024\s*x\s*1024|满幅直角|商店图标|桌面图标|启动图标", re.I)),
    ("keyart", re.compile(r"Key Art|原画主视觉|竖构图主视觉|海报主视觉", re.I)),
    ("clone_style", re.compile(r"锁风验证|风格克隆|禁止回声|只借画风", re.I)),
]

_STRONG_TOPICS = frozenset(name for name, _ in _TOPIC_PATTERNS)

_UNIVERSAL_BAN = re.compile(
    r"霓虹|赛博|油腻|过曝|漏抠|毛边|脏暗|脏色|头身|头过大|手部崩坏|塑料感|写实皮肤|毛孔|扁平无体积|灰雾废土|可读乱码",
    re.I,
)

_INJECT_REDLINE_CAP = 3
_INJECT_BAN_CAP = 5
_INJECT_KEEP_CAP = 4


def _scopes_in(text: str) -> set[str]:
    blob = text or ""
    return {name for name, pat in _TOPIC_PATTERNS if pat.search(blob)}


def _context_scopes(module: str, goal: str = "") -> set[str]:
    """Infer task scopes from module id + goal text."""
    mod = module or ""
    low = mod.lower()
    scopes = _scopes_in(f"{mod} {goal or ''}")
    dom = low.split(".", 1)[0] if low else ""
    if dom == "ui" or "hud" in low or "menu" in low:
        scopes.add("ui_shell")
    if dom == "icon" or "appicon" in low.replace(".", ""):
        scopes.add("app_icon")
    if "bird" in low:
        scopes.add("bird_merge")
    if "building" in low:
        scopes.add("building")
    if "instrument" in low:
        scopes.add("instrument")
    if "merge" in low or "ladder" in low:
        scopes.add("merge_ladder")
    if "festival" in low or ("merge" in low and any(k in low for k in ("candy", "sweet", "festival"))):
        scopes.add("candy_merge")
    if "casualbattery" in low.replace(".", "") or "mushroomcheese" in low.replace(".", ""):
        scopes.add("softcandy")
    if any(k in low for k in ("xmas", "christmas", "festival")) and "merge" not in low:
        scopes.add("xmas")
    if "keyart" in low or "fairy" in low:
        scopes.add("keyart")
    if "clone" in low or "stylelock" in low.replace(".", "") or "worldstyle" in low.replace(".", ""):
        scopes.add("clone_style")
    return scopes


def habit_relevant_for_task(habit: str, module: str, goal: str = "") -> bool:
    """Universal bans always apply; domain-specific bans only when task shares that topic."""
    text = (habit or "").strip()
    if not text:
        return False
    if _UNIVERSAL_BAN.search(text):
        return True
    habit_topics = _scopes_in(text) & _STRONG_TOPICS
    if not habit_topics:
        # No strong domain marker → treat as generic short guardrail.
        return True
    return bool(habit_topics & _context_scopes(module, goal))


def entry_on_topic_for_task(entry: dict[str, Any], module: str, goal: str = "") -> bool:
    """Drop recipes/redlines whose strong topic is absent from the current task."""
    blob = f"{entry.get('summary') or ''} {entry.get('body') or ''}"
    entry_topics = _scopes_in(blob) & _STRONG_TOPICS
    if not entry_topics:
        return True
    ctx = _context_scopes(module, goal)
    # Exclusive strong topics on the entry that the task does not carry → off-topic bleed.
    if entry_topics - ctx:
        return False
    return True


def filter_habits_for_task(habits: list[Any], module: str, goal: str = "", *, limit: int = _INJECT_BAN_CAP) -> list[str]:
    """Prefer domain-matching bans, then fill with universal; newest first within each bucket."""
    ctx = _context_scopes(module, goal)
    domain: list[str] = []
    universal: list[str] = []
    seen: set[str] = set()
    for h in reversed(list(habits or [])):
        text = str(h or "").strip()
        if not text or not habit_relevant_for_task(text, module, goal):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        topics = _scopes_in(text) & _STRONG_TOPICS
        if topics & ctx:
            domain.append(text)
        else:
            universal.append(text)
    # Reserve room for task-specific bans so universal neon/oil lists cannot crowd them out.
    domain_slots = min(len(domain), max(2, limit // 2))
    picked = domain[:domain_slots] + universal
    picked = picked[:limit]
    picked.reverse()
    return picked


def filter_keeps_for_task(keeps: list[Any], module: str, goal: str = "", *, limit: int = _INJECT_KEEP_CAP) -> list[str]:
    """Prefer constructive keep phrases; still drop hard off-topic keeps."""
    out: list[str] = []
    seen: set[str] = set()
    for k in reversed(list(keeps or [])):
        text = str(k or "").strip()
        if not text:
            continue
        topics = _scopes_in(text) & _STRONG_TOPICS
        if topics and not (topics & _context_scopes(module, goal)):
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
        if len(out) >= limit:
            break
    out.reverse()
    return out


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
        and entry_on_topic_for_task(e, module, goal)
    ]
    redlines = [
        e for e in entries
        if e.get("kind") == "style_redline"
        and _mod_ok(e.get("module", ""))
        and _entry_live(e)
        and entry_on_topic_for_task(e, module, goal)
    ]
    decisions = [
        e for e in entries
        if e.get("kind") == "art_decision"
        and _mod_ok(e.get("module", ""))
        and _entry_live(e)
        and entry_on_topic_for_task(e, module, goal)
    ]

    recipes = sorted(recipes, key=lambda e: rank_memory_entry(e, target_module=module, query=goal), reverse=True)[:top_n]
    # Rank all on-topic redlines, but only inject a short cap — excess must not crush confidence / prompt.
    redlines_ranked = sorted(
        redlines, key=lambda e: rank_memory_entry(e, target_module=module, query=goal), reverse=True
    )
    redlines = redlines_ranked[:_INJECT_REDLINE_CAP]
    decisions = sorted(decisions, key=lambda e: rank_memory_entry(e, target_module=module, query=goal), reverse=True)[:top_n]

    taste = load_taste(root)
    palette = (modules.get(module) or {}).get("palette") or []
    banned = filter_habits_for_task(taste.get("banned_habits") or [], module, goal)
    keeps = filter_keeps_for_task(taste.get("keep_phrases") or [], module, goal)

    recipe_summaries = [
        {"id": e.get("id"), "summary": e.get("summary"), "module": e.get("module")}
        for e in recipes
    ]
    redline_summaries = [
        {"id": e.get("id"), "summary": e.get("summary"), "module": e.get("module")}
        for e in redlines
    ]

    # Confidence: strong recipe match + few *injected* redlines → fast-track eligible
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
    if taste.get("preferred_lighting") or taste.get("preferred_composition") or keeps:
        conf += 0.15
        reasons.append("个人口味/正向保留非空")
    n_red = len(redlines)
    if n_red <= 3:
        conf += 0.15
        reasons.append(f"注入红线可控（{n_red} 条，已按任务主题过滤）")
    elif n_red <= 5:
        conf += 0.05
        reasons.append(f"注入红线中等（{n_red} 条）")
    else:
        reasons.append(f"注入红线较多（{n_red} 条）— 首轮需更谨慎")
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
    fast_track_eligible = conf >= 0.70 and n_red <= 5

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
    if keeps:
        prompt_block_lines.append("- 正向保留（要怎样）:")
        for k in keeps:
            prompt_block_lines.append(f"  · {k}")
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
    if taste_bits:
        prompt_block_lines.append("- 个人口味: " + "；".join(taste_bits))
    if banned:
        prompt_block_lines.append("- 个人禁用习惯（已按任务域过滤）: " + "；".join(banned))

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
            "banned_habits": banned,
            "keep_phrases": keeps,
            "banned_habits_raw_tail": (taste.get("banned_habits") or [])[-10:],
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

