"""开画前 route 闸门：没有近期本地路由结果则拒绝 converge start。

美术零门槛：他们不用管；Agent 必须先跑 route。可用 --skip-route-gate 逃生（点名调试）。
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_LAST_NAME = "last_advise.json"
_MAX_AGE_SEC = 2 * 60 * 60  # 2 小时内有效


def _path(root: Path) -> Path:
    return Path(root) / ".memory-art" / "route_bank" / _LAST_NAME


def save_route_advise(root: Path, payload: dict[str, Any], *, text: str = "") -> Path:
    dest = _path(root)
    dest.parent.mkdir(parents=True, exist_ok=True)
    blob = {
        "saved_at": time.time(),
        "text": (text or str(payload.get("plan", {}).get("steps", [{}])[0].get("deliverable") or ""))[:500],
        "banner": payload.get("banner"),
        "route_ids": payload.get("route_ids"),
        "mode": payload.get("mode"),
        "execute_ok": payload.get("execute_ok"),
        "artist_say": payload.get("artist_say"),
        "plan_conflict": payload.get("plan_conflict"),
        "confidence": payload.get("confidence"),
    }
    dest.write_text(json.dumps(blob, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return dest


def load_route_advise(root: Path) -> dict[str, Any] | None:
    path = _path(root)
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_route_gate(root: Path, *, goal: str = "") -> tuple[bool, str]:
    """返回 (ok, message)。ok=False 时不应 converge start。"""
    data = load_route_advise(root)
    if not data:
        return (
            False,
            "开画前缺少本地路由结果。请先：python3 pmem_art.py route --text \"<玩家原话>\" "
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
    # goal 弱校验：有 goal 时尽量与 text 有交集（防串台旧结果）
    g = (goal or "").strip()
    t = str(data.get("text") or "")
    if g and t and len(g) >= 4:
        # 取 goal 里较长的汉字片段粗匹配
        import re

        chunks = re.findall(r"[\u4e00-\u9fff]{2,}", g)
        if chunks and not any(c in t for c in chunks[:5]):
            # 不硬失败，只提示——避免 goal 扩写后误杀
            return True, f"提醒：上次 route 原文与当前 goal 不太像（仍放行）。route 原文：{t[:40]}"
    return True, str(data.get("banner") or "route ok")
