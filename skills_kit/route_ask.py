"""糊话 / 指代不清 → 强制问美术一句，禁止默默走普通图。

只作用在 advise_route 层，不改 plan_route（2525 回归仍按清晰话术）。
"""
from __future__ import annotations

import re
from typing import Any

from .agent_router import Plan


def _compact(text: str) -> str:
    return re.sub(r"\s+", "", text or "")


def detect_vague_ask(
    text: str,
    *,
    images: list[str] | None = None,
    plan: Plan | None = None,
) -> dict[str, str] | None:
    """若需先问人，返回 {reason, ask}；否则 None。"""
    raw = (text or "").strip()
    if not raw:
        return {
            "reason": "artist_ask_empty",
            "ask": "先说要画什么就行，例如「画一张窗边女孩水彩半身」。有参考图就一起贴上。",
        }
    pics = [p for p in (images or []) if p]
    pl = plan

    if pl is not None and pl.mode == "stop":
        return None

    # 已经认成明确专技：不再用糊话门改判
    if pl is not None and pl.mode == "skill" and pl.route_ids and pl.route_ids != ["draw.ordinary"]:
        return None

    # 图标没分档
    if re.search(r"图标|icon", raw, re.I) and not re.search(
        r"1024|桌面|启动|应用商店|线性|svg|背包|道具格|道具图标|(?<![0-9])(64|128|256)(?![0-9])",
        raw,
        re.I,
    ):
        return {
            "reason": "artist_ask_icon",
            "ask": "你要哪种图标？回一句就行：A 桌面启动 1024 / B 线性 SVG 一套 / C 背包道具格（透明底）。",
        }

    # 合成 / 继续那条，但没认成合成梯
    if re.search(r"合成梯|合成升级|一档比一档|merge\s*ladder", raw, re.I) or (
        re.search(r"合成|升级链|升档", raw) and re.search(r"继续|那条|那个|甜品|糖果|梯子|刀|剑", raw)
    ):
        if pl is None or "merge.ladder" not in (pl.route_ids or []):
            return {
                "reason": "artist_ask_merge",
                "ask": "是继续「合成梯」（同一套东西一档比一档大），还是另画一张普通图？回一句就行。",
            }

    # 指代昨天/那张/继续，又没附图
    if not pics and re.search(r"昨天|上次|刚才|之前那|那张|那条|那幅|继续(?!写)", raw):
        return {
            "reason": "artist_ask_deixis",
            "ask": "你说的「那张 / 那条 / 昨天」我这边看不到。请再贴一张参考，或把要画的对象说完整（例如「画一张窗边女孩」）。",
        }

    # 像锁风格 / 照感觉，但没样张
    if not pics and re.search(r"按这张|照这张|按昨天|味道|感觉再|以后都按|锁风格|都用这张", raw):
        return {
            "reason": "artist_ask_style_ref",
            "ask": "要按某张的画风/色板的话，请把样张贴上来；若只是新画一张，直接说「画一张××」即可。",
        }

    # 极短且没有「画一张××」骨架时才问（避免「画一张窗边女孩」被误拦）
    compact = _compact(raw)
    if len(compact) < 5 and (pl is None or pl.route_ids == ["draw.ordinary"]):
        return {
            "reason": "artist_ask_short",
            "ask": "再说具体一点：画什么？要不要参考？例如「画一张窗边女孩水彩半身」。",
        }
    if (
        len(compact) < 7
        and not re.search(r"画一张|出一张|来一张|画个|做一|帮我画", raw)
        and (pl is None or pl.route_ids == ["draw.ordinary"])
    ):
        return {
            "reason": "artist_ask_short",
            "ask": "再说具体一点：画什么？要不要参考？例如「画一张窗边女孩水彩半身」。",
        }

    return None


def artist_say_for(payload: dict[str, Any]) -> str:
    """给美术看的一两行，不含 confidence / json 字段。"""
    banner = str(payload.get("banner") or "").strip()
    ask = str(payload.get("artist_ask") or "").strip()
    if ask:
        # banner 已是「【路由停】先问你一句」
        return f"{banner}\n{ask}"
    detail = str(payload.get("artist_detail") or "").strip()
    if detail:
        return f"{banner}\n{detail}"
    return banner or "【路由】还没有结果"


def artist_detail_for(plan: Plan | None, *, route_ids: list[str] | None = None) -> str:
    ids = list(route_ids or (plan.route_ids if plan else []) or [])
    if not plan or plan.mode == "stop":
        return "先把上面那句回清，我再开始画。"
    mapping = {
        "draw.ordinary": "按普通单张来画（不是整套界面/图标/合成梯）。",
        "draw.clone": "按克隆：锁参考画风，换成新题材。",
        "draw.variant": "按变体：同一身份，换表情/动作/画风。",
        "draw.multi": "按多图分工：几张参考各管一件事。",
        "draw.lens": "按镜头包：先出几套机位给你挑，点选前不生图。",
        "draw.key": "按原画/主视觉来做。",
        "ui.kit": "按整套界面（HUD/菜单/九宫格）来做，不是单张插画。",
        "icon.a": "按桌面启动图标（1024 母版）来做。",
        "icon.b": "按线性 SVG 图标套装来做。",
        "icon.c": "按背包道具格透明底图标来做。",
        "merge.ladder": "按合成梯：先说清升级关系，再一档一张正方形。",
        "style.lock": "先锁风格/色板，这步不生图。",
        "critique.review": "只审图，不生图。",
        "atlas.file": "整理散图归档，不生图。",
        "coach.report": "看进步/短板报告，不生图。",
        "prompt.write": "先写提示词方案，这步不生图。",
    }
    if len(ids) == 1:
        return mapping.get(ids[0], "按已认的那条技能继续。")
    if len(ids) > 1:
        parts = [mapping.get(i, i) for i in ids]
        return "分步做：" + " → ".join(parts)
    return "按已认的那条技能继续。"
