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
        r"合成梯|五链合成|整表多格|邻档剪影|同域合理升级|shop_ladder|overview_sheet|"
        r"merge\s*overview|白底不可接受|禁止换物种|零件必须累计|档差要一眼|和L1一样透明|黑空底",
        re.I,
    )),
    ("softcandy", re.compile(r"草莓软糖|软糖SSS|籽粒凹|蒂叶|半透明SSS|软糖表面", re.I)),
    # Prop-icon / platter recipes bleed into portrait goals under brand.WorldStyle if unmarked.
    ("prop_icon", re.compile(
        r"prop\s*icon|透明底道具|道具格|cheese\s*platter|mushroom\s*(cheese|platter)|"
        r"红菇|果盘|真alpha|四角透明|厚剪影|角隅半透明",
        re.I,
    )),
    ("instrument", re.compile(r"乐器|竖琴|钢琴|species_change|吉他同物件", re.I)),
    ("building", re.compile(r"建筑|木屋|城堡|evermerge|庄园|吊桥|洋葱圆顶|木棚", re.I)),
    ("bird_merge", re.compile(r"鸟合成|禽类|母鸡|birds?merge|无脸抠|鸡群|翅层|尾扇", re.I)),
    ("ui_shell", re.compile(r"主菜单|HUD|九宫格|顶栏|底栏|米黄纸板|Clash底栏|设置同排|侧栏|资源栏", re.I)),
    ("app_icon", re.compile(r"App Icon|1024\s*x\s*1024|满幅直角|商店图标|桌面图标|启动图标", re.I)),
    ("keyart", re.compile(r"Key Art|原画主视觉|竖构图主视觉|海报主视觉", re.I)),
    ("fairy_garden", re.compile(
        r"妖精花园|日晒草绿|叶面绿|巨型花草|花瓣屋顶|微型花园|铃兰紫|花园拱门|巨叶",
        re.I,
    )),
    ("clone_style", re.compile(r"锁风验证|风格克隆|禁止回声|只借画风", re.I)),
    ("watercolor", re.compile(r"水彩|watercolor|wash\b|纸纹飞白|绘本立绘|湿画", re.I)),
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
    if "keyart" in low:
        scopes.add("keyart")
    if "fairy" in low or ("garden" in low and "merge" not in low):
        scopes.add("fairy_garden")
    if "clone" in low or "stylelock" in low.replace(".", "") or "worldstyle" in low.replace(".", ""):
        scopes.add("clone_style")
    if any(k in (goal or "") for k in ("水彩", "watercolor", "绘本", "wash")):
        scopes.add("watercolor")
    if any(k in low for k in ("prop", "icon")) and "appicon" not in low.replace(".", ""):
        # prop.* / icon.Prop* modules keep prop_icon recipes; brand.WorldStyle does not.
        if dom in ("prop", "icon") or "prop" in low:
            scopes.add("prop_icon")
    return scopes


_FOREIGN_ARTIFACT = re.compile(
    r"App Icon|1024\s*x\s*1024|overview_sheet|合成梯|主菜单|HUD|九宫格|"
    r"platter|prop\s*icon|currentColor|SVG 图标|桌面图标|启动图标|"
    r"整表多格|per_cell|overview\s*sheet",
    re.I,
)


def _foreign_artifact_bleed(text: str, module: str, goal: str = "") -> bool:
    """True when text is clearly another deliverable family the current task is not.

    Same-family tokens implied by module/goal scopes are stripped first, so a merge
    redline that only says「合成梯…」is not treated as foreign to merge.*.
    """
    blob = text or ""
    if not _FOREIGN_ARTIFACT.search(blob):
        return False
    task_blob = f"{module or ''} {goal or ''}"
    if _FOREIGN_ARTIFACT.search(task_blob):
        return False
    ctx = _context_scopes(module, goal)
    stripped = blob
    if "merge_ladder" in ctx or "candy_merge" in ctx or str(module or "").lower().startswith("merge."):
        stripped = re.sub(
            r"overview_sheet|合成梯|整表多格|per_cell|overview\s*sheet",
            " ",
            stripped,
            flags=re.I,
        )
    if "ui_shell" in ctx or str(module or "").lower().startswith("ui."):
        stripped = re.sub(r"主菜单|HUD|九宫格", " ", stripped, flags=re.I)
    if "app_icon" in ctx:
        stripped = re.sub(
            r"App Icon|1024\s*x\s*1024|桌面图标|启动图标",
            " ",
            stripped,
            flags=re.I,
        )
    if "prop_icon" in ctx:
        stripped = re.sub(
            r"platter|prop\s*icon|currentColor|SVG 图标",
            " ",
            stripped,
            flags=re.I,
        )
    return bool(_FOREIGN_ARTIFACT.search(stripped))


def habit_relevant_for_task(habit: str, module: str, goal: str = "") -> bool:
    """Universal bans always apply; domain-specific bans only when task shares that topic."""
    text = (habit or "").strip()
    if not text:
        return False
    if _UNIVERSAL_BAN.search(text):
        return True
    # Unmarked habits that still name another deliverable family → drop.
    if _foreign_artifact_bleed(text, module, goal):
        return False
    habit_topics = _scopes_in(text) & _STRONG_TOPICS
    if not habit_topics:
        # No strong domain marker → treat as generic short guardrail.
        return True
    return bool(habit_topics & _context_scopes(module, goal))


def _goal_tokens(goal: str) -> list[str]:
    """ASCII words + CJK bigrams so「窗边水彩半身女孩」也能做重叠判断。"""
    goal_l = (goal or "").strip().lower()
    parts = [t for t in re.split(r"[\s,，。、·:：/|+()-]+", goal_l) if t]
    out: list[str] = []
    seen: set[str] = set()
    for p in parts:
        cjk = bool(re.search(r"[\u4e00-\u9fff]", p))
        pieces = [p[i : i + 2] for i in range(len(p) - 1)] if (cjk and len(p) >= 4) else ([p] if len(p) >= 2 else [])
        for tok in pieces:
            if len(tok) < 2 or tok in seen:
                continue
            if cjk and not re.search(r"[\u4e00-\u9fff]", tok):
                continue
            seen.add(tok)
            out.append(tok)
    return out


def _soft_goal_overlap_ok(entry: dict[str, Any], goal: str, module: str = "") -> bool:
    """When entry has no strong topic tags: drop foreign-artifact bleed with 0 goal overlap.

    Vague goals / generic short redlines (no foreign artifact) still keep.
    """
    g_toks = _goal_tokens(goal)
    if len(g_toks) < 2:
        return True
    blob = f"{entry.get('summary') or ''} {entry.get('body') or ''}"
    hay = blob.lower()
    if any(t in hay for t in g_toks):
        return True
    # Another deliverable family + no goal overlap → off-topic (score optional).
    if _foreign_artifact_bleed(blob, module, goal):
        return False
    return True


def entry_on_topic_for_task(entry: dict[str, Any], module: str, goal: str = "") -> bool:
    """Drop recipes/redlines whose strong topic is absent from the current task."""
    blob = f"{entry.get('summary') or ''} {entry.get('body') or ''}"
    entry_topics = _scopes_in(blob) & _STRONG_TOPICS
    if not entry_topics:
        return _soft_goal_overlap_ok(entry, goal, module=module)
    ctx = _context_scopes(module, goal)
    # Exclusive strong topics on the entry that the task does not carry → off-topic bleed.
    if entry_topics - ctx:
        return False
    return True


def _is_merge_module(module: str) -> bool:
    return str(module or "").strip().lower().startswith("merge.")


# merge.* 注入时与现行 GH 软立体糖釉合同相反的 taste 短语
# （含「通用禁油腻」误伤糖釉；以及「平面货柜/黏土/旧光泽硬卡通」把真 GH 带歪）。
_MERGE_CONFLICT_TASTE = (
    "体量递增",
    "黑空底",
    "黑底整表",
    "纯黑隔离",
    "廉价塑料感",
    "油腻高光",
    "油腻镜面",
    "哑光缎面",
    "哑光发灰",
    # 矫枉过正：平面绘本贴纸 ≠ GH；哑光黏土 UI ≠ GH 柔光糖釉
    "平面货柜",
    "平面绘本",
    "平涂贴纸",
    "3D黏土",
    "3D 黏土",
    "黏土渲染",
    "黏土拟态",
    "claymorphism",
    # 旧缺省/旧资产文案：硬光泽卡通 3D 会把软立体糖釉带回 CGI/硬塑
    "光泽卡通 3D",
    "光泽卡通3D",
    "glossy cartoon 3D",
    "硬卡通 3D",
    "硬卡通3D",
    "硬镜面 CGI",
)

# keep 里点名他趟具体 SKU/档序身份（goal 无重叠）→ 串题材
_PRIOR_SKU_IDENTITY = re.compile(
    r"(?:HarborHotCocoa|HarborOrange|露莓果酱|冷饮店|热可可|"
    r"L1\s*(?:empty|空杯|薄纸杯)|L8\s*(?:tray|托盘)|"
    r"西瓜冰|草莓软糖SSS)",
    re.I,
)


def merge_conflict_taste_phrase(text: str) -> bool:
    """True when a taste ban/keep would push merge away from GH soft-gloss / light cards."""
    blob = str(text or "")
    return any(k in blob for k in _MERGE_CONFLICT_TASTE)


def filter_habits_for_task(habits: list[Any], module: str, goal: str = "", *, limit: int = _INJECT_BAN_CAP) -> list[str]:
    """Prefer domain-matching bans, then fill with universal; newest first within each bucket."""
    ctx = _context_scopes(module, goal)
    merge_mod = _is_merge_module(module)
    domain: list[str] = []
    universal: list[str] = []
    seen: set[str] = set()
    for h in reversed(list(habits or [])):
        text = str(h or "").strip()
        if not text or not habit_relevant_for_task(text, module, goal):
            continue
        if merge_mod and merge_conflict_taste_phrase(text):
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


def _prior_sku_bleed(text: str, goal: str) -> bool:
    """True when keep names another run's concrete SKU and goal does not share that token."""
    blob = str(text or "")
    m = _PRIOR_SKU_IDENTITY.search(blob)
    if not m:
        return False
    token = m.group(0)
    return token.lower() not in str(goal or "").lower()


def filter_keeps_for_task(keeps: list[Any], module: str, goal: str = "", *, limit: int = _INJECT_KEEP_CAP) -> list[str]:
    """Prefer constructive keep phrases; still drop hard off-topic keeps."""
    merge_mod = _is_merge_module(module)
    ctx = _context_scopes(module, goal)
    out: list[str] = []
    seen: set[str] = set()
    for k in reversed(list(keeps or [])):
        text = str(k or "").strip()
        if not text:
            continue
        if merge_mod and merge_conflict_taste_phrase(text):
            continue
        # merge 货柜任务：花园/UI 场景 keep 不得灌进道具整表
        if merge_mod and ("fairy_garden" in (_scopes_in(text) & _STRONG_TOPICS)):
            if "merge_ladder" not in (_scopes_in(text) & _STRONG_TOPICS) and not re.search(
                r"货柜|糖釉|Gossip\s*Harbor|玩具货柜", text, re.I
            ):
                continue
        if _foreign_artifact_bleed(text, module, goal):
            continue
        if _prior_sku_bleed(text, goal):
            continue
        topics = _scopes_in(text) & _STRONG_TOPICS
        if topics and not (topics & ctx):
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


_COLD_MARK = re.compile(r"冷光|冷色|冷光源|冷色调")
_WARM_MARK = re.compile(r"暖光|暖色|暖色调|暖光源")


def collapse_opposed_prefs(vals: list[Any], *, limit: int = 3) -> list[str]:
    """Drop simultaneous cold+warm taste lists that cancel each other in the prompt.

    Keep the newest polarity only when both cold and warm appear in the recent tail.
    """
    cleaned = [str(v or "").strip() for v in (vals or []) if str(v or "").strip()]
    if not cleaned:
        return []
    tail = cleaned[-max(limit, 3) :]
    has_cold = any(_COLD_MARK.search(v) for v in tail)
    has_warm = any(_WARM_MARK.search(v) for v in tail)
    if not (has_cold and has_warm):
        return cleaned[-limit:]
    last = tail[-1]
    if _COLD_MARK.search(last) and not _WARM_MARK.search(last):
        picked = [v for v in cleaned if not _WARM_MARK.search(v)]
    elif _WARM_MARK.search(last) and not _COLD_MARK.search(last):
        picked = [v for v in cleaned if not _COLD_MARK.search(v)]
    else:
        picked = [last]
    return picked[-limit:]


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


_STALE_MERGE_VOLUME = (
    "框高阶梯",
    "框高递增",
    "末档最大",
    "末档不是最大",
    "邻档主体框高",
    "只拉开框高",
    # 旧闸量出的数字/回退句：注入会逼 agent 凑框高
    "机读框高",
    "框高约",
    "框高L",
    "体量递增",
)
_STALE_MERGE_BLACK = ("纯黑隔离底", "黑空底", "黑底整表")


def stale_merge_inject_summary(entry: dict[str, Any]) -> bool:
    """merge.* 条目的 summary 若仍推销旧体量闸/纯黑整表底，不进暖启注入。

    只看 summary（注入包实际用的字段），不改记忆文件正文。
    """
    if not str(entry.get("module") or "").startswith("merge."):
        return False
    summary = str(entry.get("summary") or "")
    return any(k in summary for k in _STALE_MERGE_VOLUME + _STALE_MERGE_BLACK)


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

    def _stale_merge_phrase(e: dict) -> bool:
        """merge 旧闸 summary 不进注入：框高阶梯 / 纯黑整表底与现行合同相反。"""
        return stale_merge_inject_summary(e)

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
        and not _stale_merge_phrase(e)
        and _recipe_ok_for_shell_goal(e)
        and entry_on_topic_for_task(e, module, goal)
    ]
    redlines = [
        e for e in entries
        if e.get("kind") == "style_redline"
        and _mod_ok(e.get("module", ""))
        and _entry_live(e)
        and not _stale_merge_phrase(e)
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
    # Drop hard medium clashes + strong-topic / foreign-artifact bleed into prompts.
    ctx_scopes = _context_scopes(module, goal)
    def _knowledge_ok(card: dict[str, Any]) -> bool:
        blob = f"{card.get('title') or ''} {card.get('body') or ''}"
        if "watercolor" in ctx_scopes and re.search(r"赛璐珞|cel.?shade|硬边色块分层", blob, re.I):
            return False
        if "prop_icon" not in ctx_scopes and re.search(r"prop\s*icon|真alpha|cheese\s*platter", blob, re.I):
            return False
        card_topics = _scopes_in(blob) & _STRONG_TOPICS
        if card_topics - ctx_scopes:
            return False
        if _foreign_artifact_bleed(blob, module, goal):
            return False
        return True

    recalled_cards = [c for c in recalled_cards if _knowledge_ok(c)]
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
        "- 注：同模块旧 recipe 只参与置信，不进生图词（避免「优先复用」把旧题材/旧档序当成本趟底稿）。",
    ]
    # recipe_summaries intentionally omitted from prompt_block (kept on pack for UI/confidence).
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
        raw_vals = taste.get(key) or []
        vals = (
            collapse_opposed_prefs(raw_vals, limit=3)
            if key in ("preferred_lighting", "preferred_color_temperature")
            else [str(v).strip() for v in raw_vals if str(v).strip()][-3:]
        )
        if vals:
            taste_bits.append(f"{label}={' / '.join(vals)}")
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
            "preferred_lighting": collapse_opposed_prefs(
                taste.get("preferred_lighting", []), limit=5
            ),
            "preferred_composition": (taste.get("preferred_composition", []) or [])[-5:],
            "preferred_line_weight": (taste.get("preferred_line_weight", []) or [])[-5:],
            "preferred_color_temperature": collapse_opposed_prefs(
                taste.get("preferred_color_temperature", []), limit=5
            ),
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

