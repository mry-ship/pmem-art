"""Active converge session slot gate (agent.max_parallel)."""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any

# finished 不占槽。prepare 中途失败且还没有成图时记 prepare_aborted，同样不占槽。
_TERMINAL = frozenset({"finished", "prepare_aborted"})
# 心跳状态。lost 是确认失联，不再占槽。其余状态靠 heartbeat_at，不看文件 mtime。
HEARTBEAT_STATES = ("generating", "waiting_model", "awaiting_human", "lost")
# 预占只挡住「会话文件还没写出来」的窗口。崩溃留下的预占过期后不再占槽。
RESERVE_TTL_SEC = 15 * 60
_SAFE_ID = re.compile(r"[^A-Za-z0-9._-]+")


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


def _heartbeat_dir(root: Path) -> Path:
    return Path(root) / ".memory-art" / "converge" / "_heartbeats"


def _corrupt_dir(root: Path) -> Path:
    return Path(root) / ".memory-art" / "converge" / "_corrupt"


def write_heartbeat(root: Path, session_id: str, state: str) -> None:
    """Refresh liveness without rewriting the session file or its mtime."""
    sid = (session_id or "").strip()
    if not sid:
        return
    phase = state if state in HEARTBEAT_STATES else "generating"
    folder = _heartbeat_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    payload = {"session_id": sid, "state": phase, "at": time.time()}
    path = folder / f"{_safe_session_id(sid)}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def read_heartbeat(root: Path, session_id: str) -> dict[str, Any] | None:
    sid = (session_id or "").strip()
    if not sid:
        return None
    path = _heartbeat_dir(root) / f"{_safe_session_id(sid)}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _epoch_of(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        number = float(value)
        if number > 10_000:
            return number
    text = str(value or "").strip()
    if not text:
        return None
    try:
        number = float(text)
    except ValueError:
        number = 0.0
    else:
        if number > 10_000:
            return number
    core = text.replace("UTC+8", "").strip()
    try:
        from datetime import datetime

        return datetime.strptime(core, "%Y-%m-%d %H:%M:%S").timestamp()
    except ValueError:
        return None


def _liveness(root: Path, session_id: str, sess: dict[str, Any]) -> tuple[str, float | None]:
    side = read_heartbeat(root, session_id) or {}
    side_at = _epoch_of(side.get("at"))
    side_state = str(side.get("state") or "")
    sess_at = _epoch_of(sess.get("heartbeat_at"))
    sess_state = str(sess.get("heartbeat_state") or "")
    if side_at is not None and (sess_at is None or side_at >= sess_at):
        state = side_state if side_state in HEARTBEAT_STATES else (sess_state or "generating")
        return state, side_at
    if sess_at is not None:
        state = sess_state if sess_state in HEARTBEAT_STATES else "generating"
        return state, sess_at
    started = _epoch_of(sess.get("started_at"))
    if started is not None:
        state = sess_state if sess_state in HEARTBEAT_STATES else "generating"
        return state, started
    return sess_state or "generating", None


def isolate_corrupt_session(root: Path, path: Path, error: str) -> dict[str, Any]:
    """Move a broken session aside and keep holding its slot until someone releases it."""
    folder = _corrupt_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    sid = path.stem
    hold_path = folder / f"{_safe_session_id(sid)}.hold.json"
    record: dict[str, Any] = {
        "session_id": sid,
        "status": "corrupt",
        "error": (error or "")[:500],
        "holds_slot": True,
        "isolated_at": time.time(),
        "isolated_path": "",
    }
    dest = folder / path.name
    if dest.exists():
        dest = folder / f"{path.stem}-{int(time.time())}{path.suffix}"
    try:
        path.replace(dest)
        record["isolated_path"] = str(dest)
    except OSError as exc:
        record["isolated_path"] = str(path)
        record["error"] = f"{record['error']}; 隔离失败: {exc}"[:500]
    hold_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    with (folder / "log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def list_corrupt_holds(root: Path) -> list[dict[str, Any]]:
    folder = _corrupt_dir(root)
    if not folder.is_dir():
        return []
    out: list[dict[str, Any]] = []
    for path in sorted(folder.glob("*.hold.json")):
        try:
            rec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(rec, dict) or not rec.get("holds_slot"):
            continue
        out.append(
            {
                "session_id": str(rec.get("session_id") or path.name.replace(".hold.json", "")),
                "status": "corrupt",
                "path": str(rec.get("isolated_path") or path),
                "module": "",
                "error": str(rec.get("error") or ""),
            }
        )
    return out


def release_corrupt_slot(root: Path, session_id: str) -> bool:
    """Drop a corrupt hold after a person confirms it or the file is restored."""
    sid = (session_id or "").strip()
    if not sid:
        return False
    path = _corrupt_dir(root) / f"{_safe_session_id(sid)}.hold.json"
    if not path.is_file():
        return False
    try:
        rec = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        rec = {"session_id": sid}
    if not isinstance(rec, dict):
        rec = {"session_id": sid}
    rec["holds_slot"] = False
    rec["released_at"] = time.time()
    path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
    return True


def list_active_sessions(root: Path, data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Non-finished sessions, plus corrupt files that still hold a slot.

    Freshness uses heartbeat_at / the heartbeat sidecar / started_at.
    File mtime is not a running state. lost does not hold a slot.
    Corrupt JSON is isolated and keeps the slot until release_corrupt_slot.
    """
    d = root / ".memory-art" / "converge"
    if not d.is_dir():
        return []
    stale_sec = slot_stale_seconds(data)
    now = time.time()
    out: list[dict[str, Any]] = []
    held: set[str] = set()
    for p in sorted(d.glob("*.json")):
        if p.name.endswith(".tmp") or p.name.startswith("_"):
            continue
        try:
            sess = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rec = isolate_corrupt_session(root, p, f"JSONDecodeError: {exc}")
            sid = str(rec.get("session_id") or p.stem)
            if sid not in held:
                held.add(sid)
                out.append(
                    {
                        "session_id": sid,
                        "status": "corrupt",
                        "path": str(rec.get("isolated_path") or p),
                        "module": "",
                    }
                )
            continue
        except OSError:
            continue
        if not isinstance(sess, dict):
            rec = isolate_corrupt_session(root, p, "会话 JSON 不是对象")
            sid = str(rec.get("session_id") or p.stem)
            if sid not in held:
                held.add(sid)
                out.append(
                    {
                        "session_id": sid,
                        "status": "corrupt",
                        "path": str(rec.get("isolated_path") or p),
                        "module": "",
                    }
                )
            continue
        status = str(sess.get("status") or "").strip()
        if not status or status in _TERMINAL:
            continue
        sid = str(sess.get("session_id") or p.stem)
        state, beat = _liveness(root, sid, sess)
        if state == "lost":
            continue
        if stale_sec > 0 and beat is not None and now - beat > stale_sec:
            continue
        if sid in held:
            continue
        held.add(sid)
        out.append(
            {
                "session_id": sid,
                "status": status,
                "path": str(p),
                "module": str(sess.get("module") or ""),
                "heartbeat_state": state,
            }
        )
    for item in list_corrupt_holds(root):
        sid = str(item["session_id"])
        if sid in held:
            continue
        held.add(sid)
        out.append(item)
    return out


def _slot_sentinel(root: Path) -> Path:
    return Path(root) / ".memory-art" / "converge" / "_slot_gate.json"


def _slots_dir(root: Path) -> Path:
    d = Path(root) / ".memory-art" / "converge" / "_slots"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _safe_session_id(session_id: str) -> str:
    sid = (session_id or "").strip() or "session"
    cleaned = _SAFE_ID.sub("_", sid).strip("._") or "session"
    return cleaned[:80]


def _reserve_path(root: Path, session_id: str) -> Path:
    return _slots_dir(root) / f"{_safe_session_id(session_id)}.reserve.json"


def purge_expired_reservations(root: Path, *, now: float | None = None) -> int:
    """Delete reservations older than RESERVE_TTL_SEC. Returns how many were removed."""
    d = Path(root) / ".memory-art" / "converge" / "_slots"
    if not d.is_dir():
        return 0
    clock = time.time() if now is None else now
    removed = 0
    for path in d.glob("*.reserve.json"):
        expired = False
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            started = float(payload.get("reserved_at") or 0)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            expired = True
            started = 0.0
        if not expired and (started <= 0 or clock - started > RESERVE_TTL_SEC):
            expired = True
        if expired:
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def list_reservations(root: Path, *, now: float | None = None) -> list[dict[str, Any]]:
    """Live reservations. Does not purge; callers that decide a slot hold the gate lock."""
    d = Path(root) / ".memory-art" / "converge" / "_slots"
    if not d.is_dir():
        return []
    clock = time.time() if now is None else now
    out: list[dict[str, Any]] = []
    for path in sorted(d.glob("*.reserve.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            started = float(payload.get("reserved_at") or 0)
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            continue
        if started <= 0 or clock - started > RESERVE_TTL_SEC:
            continue
        sid = str(payload.get("session_id") or path.name.replace(".reserve.json", ""))
        out.append(
            {
                "session_id": sid,
                "status": "reserved",
                "path": str(path),
                "module": "",
                "reserved_at": started,
            }
        )
    return out


def list_slot_holders(root: Path, data: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Active sessions plus reservations whose session file is not already holding a slot."""
    sessions = list_active_sessions(root, data)
    held = {str(item["session_id"]) for item in sessions}
    extras = [item for item in list_reservations(root) if item["session_id"] not in held]
    return sessions + extras


def _deny_message(others: list[dict[str, Any]], limit: int) -> str:
    names = "、".join(a["session_id"] for a in others[:6])
    more = "" if len(others) <= 6 else f" 等{len(others)}个"
    return (
        f"并行槽已满（活跃 {len(others)}/{limit}）：{names}{more}。"
        f"先 finish 或等终态后再 start；可改 .memory-art/config.yaml → agent.max_parallel。"
    )


def _decide_start(
    root: Path,
    data: dict[str, Any] | None,
    *,
    session_id: str,
    reuse_same: bool,
) -> tuple[bool, str]:
    limit = max_parallel(data)
    holders = list_slot_holders(root, data)
    sid = (session_id or "").strip()
    others = [a for a in holders if a["session_id"] != sid] if reuse_same else holders
    if len(others) >= limit:
        return False, _deny_message(others, limit)
    already = any(a["session_id"] == sid for a in holders)
    return True, f"并行槽 {len(others) + (0 if already else 1)}/{limit}"


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
    Counts live reservations so a start that has claimed a slot but not written
    the session yet is visible. The check itself is not the claim.
    """
    from .session_lock import session_file_lock

    with session_file_lock(_slot_sentinel(root)):
        purge_expired_reservations(root)
        return _decide_start(root, data, session_id=session_id, reuse_same=reuse_same)


def reserve_slot(
    root: Path,
    data: dict[str, Any] | None,
    *,
    session_id: str,
    reuse_same: bool = True,
    token: str = "",
) -> tuple[bool, str]:
    """Atomically claim one slot before the session file exists.

    The lock covers purge, the count, and the reservation write.
    ``token`` identifies this claim. A later release with another token
    leaves this file alone.
    """
    from .session_lock import session_file_lock

    sid = (session_id or "").strip()
    claim = (token or "").strip() or uuid.uuid4().hex
    with session_file_lock(_slot_sentinel(root)):
        purge_expired_reservations(root)
        ok, msg = _decide_start(root, data, session_id=sid, reuse_same=reuse_same)
        if not ok:
            return False, msg
        path = _reserve_path(root, sid)
        payload = {
            "session_id": sid,
            "reserved_at": time.time(),
            "pid": os.getpid(),
            "token": claim,
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, path)
        return True, msg


def commit_slot(root: Path, session_id: str, *, token: str = "") -> None:
    """Session file now holds the slot. Drop the pre-claim."""
    release_slot(root, session_id, token=token)


def release_slot(root: Path, session_id: str, *, token: str = "") -> None:
    """Drop a pre-claim after a failed start. Missing files are fine.

    A non-empty ``token`` only deletes the reservation written by that claim.
    An empty token deletes whatever reservation is stored for this id.
    """
    from .session_lock import session_file_lock

    path = _reserve_path(root, session_id)
    with session_file_lock(_slot_sentinel(root)):
        if token:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                return
            if str(payload.get("token") or "") != token:
                return
        try:
            path.unlink()
        except OSError:
            pass


class SlotClaim:
    """Reserve on enter-success, release unless commit() ran."""

    def __init__(self, root: Path, data: dict[str, Any] | None, session_id: str):
        self.root = root
        self.session_id = session_id
        self.token = uuid.uuid4().hex
        self.ok, self.msg = reserve_slot(
            root, data, session_id=session_id, token=self.token
        )
        self._open = self.ok

    def commit(self) -> None:
        if self._open:
            commit_slot(self.root, self.session_id, token=self.token)
            self._open = False

    def close(self) -> None:
        if self._open:
            release_slot(self.root, self.session_id, token=self.token)
            self._open = False

    def __enter__(self) -> "SlotClaim":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()
