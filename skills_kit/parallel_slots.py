"""Active converge session slot gate (agent.max_parallel)."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

_TERMINAL = frozenset({"finished"})


def max_parallel(data: dict[str, Any] | None = None, *, default: int = 4) -> int:
    cfg = ((data or {}).get("config") or {}).get("agent") or {}
    try:
        n = int(cfg.get("max_parallel") if cfg.get("max_parallel") is not None else default)
    except (TypeError, ValueError):
        n = default
    return max(1, min(8, n))


def slot_stale_seconds(data: dict[str, Any] | None) -> float:
    """Ignore non-finished sessions older than this. 0 disables the ignore."""
    cfg = ((data or {}).get("config") or {}).get("agent") or {}
    raw = cfg.get("slot_stale_hours", 36)
    try:
        hours = float(raw)
    except (TypeError, ValueError):
        hours = 36.0
    if hours <= 0:
        return 0.0
    return hours * 3600.0


def list_active_sessions(root: Path, data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Scan `.memory-art/converge/*.json` for non-finished sessions.

    Files older than agent.slot_stale_hours (default 36) do not hold a slot.
    Their JSON is left unchanged.
    """
    d = root / ".memory-art" / "converge"
    if not d.is_dir():
        return []
    stale_sec = slot_stale_seconds(data)
    now = time.time()
    out: list[dict[str, Any]] = []
    for p in sorted(d.glob("*.json")):
        if p.name.endswith(".tmp") or p.name.startswith("_"):
            continue
        try:
            sess = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(sess, dict):
            continue
        status = str(sess.get("status") or "").strip()
        if not status or status in _TERMINAL:
            continue
        if stale_sec > 0:
            try:
                if now - p.stat().st_mtime > stale_sec:
                    continue
            except OSError:
                continue
        # 未过期的非 finished 一律占槽（含 converged 等 finish、early_safe_stop）
        sid = str(sess.get("session_id") or p.stem)
        out.append(
            {
                "session_id": sid,
                "status": status,
                "path": str(p),
                "module": str(sess.get("module") or ""),
            }
        )
    return out


def assert_can_start(
    root: Path,
    data: dict[str, Any] | None,
    *,
    session_id: str,
    reuse_same: bool = True,
) -> tuple[bool, str]:
    """
    Hard gate: refuse opening another quality session when active count >= max_parallel.
    Re-starting the same session_id (overwrite / continue) is allowed.
    """
    limit = max_parallel(data)
    active = list_active_sessions(root, data)
    sid = (session_id or "").strip()
    others = [a for a in active if a["session_id"] != sid] if reuse_same else active
    if len(others) >= limit:
        names = "、".join(a["session_id"] for a in others[:6])
        more = "" if len(others) <= 6 else f" 等{len(others)}个"
        return (
            False,
            f"并行槽已满（活跃 {len(others)}/{limit}）：{names}{more}。"
            f"先 finish 或等终态后再 start；可改 .memory-art/config.yaml → agent.max_parallel。",
        )
    return True, f"并行槽 {len(others) + (0 if any(a['session_id']==sid for a in active) else 1)}/{limit}"
