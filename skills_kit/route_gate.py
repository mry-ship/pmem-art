"""开画前 route 闸门：没有近期本地路由结果则拒绝 converge start。

美术零门槛：他们不用管；Agent 必须先跑 route。可用 --skip-route-gate 逃生（点名调试）。
"""
from __future__ import annotations

from .platform_cli import pmem_art_cli
import json
import time
from pathlib import Path
from typing import Any

_LAST_NAME = "last_advise.json"
_MAX_AGE_SEC = 2 * 60 * 60  # 2 小时内有效


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
    raw = json.dumps(blob, ensure_ascii=False, indent=2) + "\n"
    dest.write_text(raw, encoding="utf-8")
    cid = (conversation_id or "").strip()
    if cid:
        slot = _conv_path(root, cid)
        slot.parent.mkdir(parents=True, exist_ok=True)
        slot.write_text(raw, encoding="utf-8")
    return dest


def load_route_advise(root: Path, conversation_id: str = "") -> dict[str, Any] | None:
    cid = (conversation_id or "").strip()
    if cid:
        slot = _read_json(_conv_path(root, cid))
        if slot:
            return slot
    data = _read_json(_path(root))
    if not data:
        return None
    owner = str(data.get("conversation_id") or "").strip()
    if owner and owner != cid:
        return {"_foreign": True, "conversation_id": owner}
    return data


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
    if not data:
        return (
            False,
            f"开画前缺少本地路由结果。请先：{pmem_art_cli()} route --text \"<玩家原话>\" "
            "[--canonical \"<标准句>\"] [--brief]；点名调试可加 --skip-route-gate。",
        )
    age = time.time() - float(data.get("saved_at") or 0)
    if age > _MAX_AGE_SEC:
        return (
            False,
            f"本地路由结果已过期（{int(age // 60)} 分钟前）。请对当前这句话重新跑 route。",
        )
    if data.get("mode") == "stop" or data.get("execute_ok") is False:
        ask = str(data.get("artist_say") or data.get("banner") or "路由未放行")
        return False, f"路由尚未放行，不能开画。{ask}"
    saved_ids = [str(x) for x in (data.get("route_ids") or []) if str(x)]
    want = (expect_route or "").strip()
    if want and want not in saved_ids:
        shown = "、".join(saved_ids) or "（空）"
        return False, f"本次要开的是 {want}，上次路由是 {shown}。请对当前这句话重新跑 route。"
    g = (goal or "").strip()
    t = str(data.get("text") or "")
    if match_goal and g and t and len(g) >= 4:
        import re

        chunks = re.findall(r"[\u4e00-\u9fff]{4,}", g)
        if chunks and any(c not in t for c in chunks):
            return False, f"上次 route 原文与当前 goal 对不上，请重新 route。route 原文：{t[:40]}"
    return True, str(data.get("banner") or "route ok")
