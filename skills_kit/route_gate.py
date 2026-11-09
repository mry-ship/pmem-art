"""开画前 route 闸门：没有近期本地路由结果则拒绝 converge start。

美术零门槛：他们不用管；Agent 必须先跑 route。调试跳闸见 gate_skip（ALLOW + --skip-reason）。

点名锁定：`converge start --route-id <已知路由>` 仅在**无缓存/已过期**时可自动种闸；
已有新鲜且路由不一致的缓存时必须重跑 route，禁止静默覆盖。
"""
from __future__ import annotations

from .platform_cli import pmem_art_cli
import json
import re
import time
from pathlib import Path
from typing import Any

_LAST_NAME = "last_advise.json"
_MAX_AGE_SEC = 2 * 60 * 60  # 2 小时内有效

# 可点名种闸的 route_id（与 reasonableness ROUTE_TO_REVIEW_SKILL 对齐）
_SEEDABLE_ROUTES = frozenset(
    {
        "draw.ordinary",
        "draw.key",
        "draw.clone",
        "draw.variant",
        "draw.multi",
        "draw.lens",
        "ui.kit",
        "icon.a",
        "icon.b",
        "icon.c",
        "merge.ladder",
        "style.lock",
        "critique.review",
        "atlas.file",
        "coach.report",
        "prompt.write",
    }
)

# 斜杠技能里子类型唯一的可从 goal 推断；/pmem-draw / /pmem-icon 须显式 --route-id
_SLASH_TO_ROUTE: dict[str, str] = {
    "/pmem-ui": "ui.kit",
    "/pmem-merge-ladder": "merge.ladder",
    "/pmem-style-lock": "style.lock",
    "/pmem-critique": "critique.review",
    "/pmem-atlas": "atlas.file",
    "/pmem-coach": "coach.report",
    "/pmem-prompt": "prompt.write",
}


def _path(root: Path) -> Path:
    return Path(root) / ".memory-art" / "route_bank" / _LAST_NAME


def _conv_path(root: Path, conversation_id: str) -> Path:
    safe = "".join(ch for ch in conversation_id if ch.isalnum() or ch in "-_")[:80]
    return Path(root) / ".memory-art" / "route_bank" / "by_conversation" / f"{safe}.json"


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def save_route_advise(
    root: Path,
    payload: dict[str, Any],
    *,
    text: str = "",
    conversation_id: str = "",
) -> Path:
    dest = _path(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = {
        "saved_at": time.time(),
        "text": (text or str(payload.get("plan", {}).get("steps", [{}])[0].get("deliverable") or ""))[:8000],
        "banner": payload.get("banner"),
        "route_ids": payload.get("route_ids"),
        "mode": payload.get("mode"),
        "execute_ok": payload.get("execute_ok"),
        "artist_say": payload.get("artist_say"),
        "plan_conflict": payload.get("plan_conflict"),
        "confidence": payload.get("confidence"),
        "conversation_id": (conversation_id or "").strip(),
    }
    if payload.get("named_seed"):
        blob["named_seed"] = True
    raw = json.dumps(blob, ensure_ascii=False, indent=2) + "\n"
    cid = (conversation_id or "").strip()
    if cid:
        # 有对话窗：只写分槽，禁止覆盖全局 last_advise（并发多技能会互相踩闸）
        slot = _conv_path(root, cid)
        slot.parent.mkdir(parents=True, exist_ok=True)
        slot.write_text(raw, encoding="utf-8")
        return slot
    dest.write_text(raw, encoding="utf-8")
    return dest


def load_route_advise(root: Path, conversation_id: str = "") -> dict[str, Any] | None:
    cid = (conversation_id or "").strip()
    if cid:
        # 有对话窗：只认分槽。无分槽时 fail-closed，禁止回落全局（并发串闸）。
        return _read_json(_conv_path(root, cid))
    data = _read_json(_path(root))
    if not data:
        return None
    owner = str(data.get("conversation_id") or "").strip()
    if owner and owner != cid:
        return {"_foreign": True, "conversation_id": owner}
    return data


def resolve_named_route_id(*, goal: str = "", expect_route: str = "") -> str:
    """从 --route-id 或唯一斜杠技能推断可种闸的 route_id；推不出则空串。"""
    want = (expect_route or "").strip()
    if want in _SEEDABLE_ROUTES:
        return want
    g = goal or ""
    low = g.lower()
    for slash, rid in _SLASH_TO_ROUTE.items():
        if slash in low or slash in g:
            return rid
    return ""


def seed_named_route(
    root: Path,
    route_id: str,
    *,
    goal: str = "",
    conversation_id: str = "",
) -> Path:
    """按点名锁定写入闸门缓存（execute_ok=true）。"""
    rid = (route_id or "").strip()
    banner = f"【按点名锁定 {rid}】"
    payload = {
        "banner": banner,
        "route_ids": [rid],
        "mode": "default" if rid == "draw.ordinary" else "skill",
        "execute_ok": True,
        "artist_say": banner,
        "plan_conflict": False,
        "confidence": "named",
        "named_seed": True,
    }
    return save_route_advise(
        root,
        payload,
        text=(goal or f"named:{rid}")[:8000],
        conversation_id=conversation_id,
    )


def goal_match_tokens(goal: str) -> list[str]:
    """从 goal 抽匹配锚点：中文≥2 字、英文≥3 字母、≥2 位数字。

    旧实现只抽中文≥4，英文/「出图」「糖果」抽不出 → 内容校验被跳过而误放行。
    """
    g = (goal or "").strip()
    if not g:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def _add(tok: str) -> None:
        key = tok.lower()
        if key in seen:
            return
        seen.add(key)
        out.append(tok)

    for m in re.findall(r"[\u4e00-\u9fff]{2,}", g):
        _add(m)
    for m in re.findall(r"[A-Za-z]{3,}", g):
        _add(m.lower())
    for m in re.findall(r"\d{2,}", g):
        _add(m)
    return out


def _heavy_missing(tokens: list[str], haystack: str) -> list[str]:
    """返回未出现在 haystack 中的重锚点（中文≥2 / 英文≥3 / 数字≥2）。"""
    h_low = (haystack or "").lower()
    missing = [tok for tok in tokens if tok.lower() not in h_low and tok not in haystack]
    return [
        m
        for m in missing
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", m)
        or re.fullmatch(r"[a-z]{3,}", m.lower())
        or re.fullmatch(r"\d{2,}", m)
        or re.fullmatch(r"[\u4e00-\u9fff]{2,3}", m)
    ]


def goal_matches_route_text(goal: str, route_text: str) -> tuple[bool, str]:
    """True 当 goal 与 route 原文对得上。

    规则（兼容同题扩写，拦住换题）：
    1) 归一化后互相包含 → 过（goal 扩写含 route 原文，或 route 含 goal）
    2) route 锚点全落在 goal → 过（开画 goal 常比 route 句更长）
    3) goal 锚点全落在 route → 过（短 goal / 旧行为）
    4) 否则拦
    """
    g = (goal or "").strip()
    t = (route_text or "").strip()
    if not g or not t:
        return True, ""
    # 极短 goal（<2）无法可靠匹配 → 与原文不等则拦
    if len(g) < 2:
        if g not in t:
            return False, f"goal 过短且不在 route 原文中：{g!r}"
        return True, ""
    gn = re.sub(r"\s+", "", g).lower()
    tn = re.sub(r"\s+", "", t).lower()
    if gn in tn or tn in gn:
        return True, ""

    route_tokens = goal_match_tokens(t)
    if route_tokens and not _heavy_missing(route_tokens, g):
        return True, ""

    tokens = goal_match_tokens(g)
    if tokens and not _heavy_missing(tokens, t):
        return True, ""

    if not tokens and not route_tokens:
        return False, "goal 与 route 原文无法对齐（无可用锚点）"
    # 优先报「换题」：route 锚点不在 goal
    if route_tokens:
        heavy = _heavy_missing(route_tokens, g)
        if heavy:
            shown = "、".join(heavy[:6])
            return False, f"route 原文锚点未出现在 goal：{shown}"
    heavy = _heavy_missing(tokens, t) if tokens else []
    if heavy:
        shown = "、".join(heavy[:6])
        return False, f"goal 锚点未出现在 route 原文：{shown}"
    return False, "goal 与 route 原文无法对齐"


def check_route_gate(
    root: Path,
    *,
    goal: str = "",
    expect_route: str = "",
    conversation_id: str = "",
    match_goal: bool = True,
) -> tuple[bool, str]:
    """返回 (ok, message)。ok=False 时不应开画。"""
    data = load_route_advise(root, conversation_id)
    if data and data.get("_foreign"):
        return False, "上次路由属于另一对话。请对当前这句话重新跑 route。"

    named_id = resolve_named_route_id(goal=goal, expect_route=expect_route)

    def _try_named_seed(why: str) -> tuple[bool, str] | None:
        """仅无缓存/过期时可种闸；禁止覆盖新鲜且路由不一致的缓存。

        若 goal 按规则会 stop（序列帧/分镜问句等），禁止 --route-id 静默种闸硬开画。
        """
        if not named_id:
            return None
        g = (goal or "").strip()
        if g:
            from .agent_router import plan_route

            probe = plan_route(g)
            if probe.mode == "stop":
                detail = (probe.announce or probe.reason or "stop").strip()
                return (
                    False,
                    f"{why}点名种闸被拒绝：规则路由为 stop（{probe.reason}）。{detail}"
                    " 请改口或先 route，禁止用 --route-id 绕过停闸。",
                )
            probe_ids = [str(x) for x in (probe.route_ids or []) if str(x)]
            if probe_ids and named_id not in probe_ids:
                shown = "、".join(probe_ids)
                return (
                    False,
                    f"{why}点名种闸被拒绝：规则路由是 {shown}，与 --route-id {named_id} 不一致。"
                    " 请对当前这句话重跑 route，禁止用 --route-id 静默换支。",
                )
        seed_named_route(root, named_id, goal=goal, conversation_id=conversation_id)
        return (
            True,
            f"{why}已按点名种闸 route_id={named_id}（仍建议正式跑 route；禁止用 --skip-route-gate 代替）。",
        )

    if not data:
        seeded = _try_named_seed("开画前缺少本地路由结果；")
        if seeded:
            return seeded
        hint = ""
        g = (goal or "").lower()
        if "/pmem-draw" in g or "/pmem-icon" in g:
            hint = (
                " 点名 /pmem-draw 或 /pmem-icon 时请先 route，"
                "或在 converge start 加 --route-id（如 draw.ordinary / icon.a）。"
            )
        return (
            False,
            f"开画前缺少本地路由结果。请先：{pmem_art_cli()} route --text \"<玩家原话>\" "
            f"[--canonical \"<标准句>\"] [--brief]；或 converge start --route-id <路由> 点名种闸。"
            f"{hint}",
        )
    age = time.time() - float(data.get("saved_at") or 0)
    if age > _MAX_AGE_SEC:
        # 过期且 route_id 与缓存不一致：禁止静默换路由（与新鲜冲突对称）
        saved_ids_expired = [str(x) for x in (data.get("route_ids") or []) if str(x)]
        if named_id and saved_ids_expired and named_id not in saved_ids_expired:
            shown = "、".join(saved_ids_expired) or "（空）"
            return (
                False,
                f"本地路由已过期（{int(age // 60)} 分钟前），上次是 {shown}、本次要 {named_id}。"
                "请对当前这句话重新跑 route（禁止过期后用 --route-id 静默换路由）。",
            )
        seeded = _try_named_seed(f"本地路由结果已过期（{int(age // 60)} 分钟前）；")
        if seeded:
            return seeded
        return (
            False,
            f"本地路由结果已过期（{int(age // 60)} 分钟前）。请对当前这句话重新跑 route。"
            "或 converge start --route-id <路由> 点名种闸。",
        )
    if data.get("mode") == "stop" or data.get("execute_ok") is False:
        ask = str(data.get("artist_say") or data.get("banner") or "路由未放行")
        return False, f"路由尚未放行，不能开画。{ask}"
    saved_ids = [str(x) for x in (data.get("route_ids") or []) if str(x)]
    want = (expect_route or "").strip()
    if want and want not in saved_ids:
        # 新鲜缓存路由不一致：必须重跑 route，禁止 --route-id 静默覆盖（防半失效锁）
        shown = "、".join(saved_ids) or "（空）"
        return False, f"本次要开的是 {want}，上次路由是 {shown}。请对当前这句话重新跑 route。"
    g = (goal or "").strip()
    t = str(data.get("text") or "")
    if match_goal and g and t:
        ok_match, why = goal_matches_route_text(g, t)
        if not ok_match:
            # 有新鲜缓存时不对 goal 漂移做点名覆盖；要求重 route
            return False, f"上次 route 原文与当前 goal 对不上，请重新 route。{why}；route 原文：{t[:40]}"
    return True, str(data.get("banner") or "route ok")
