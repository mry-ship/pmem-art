"""Force the generate → judge → next-round loop without relying on agent memory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .showcase_gate import DEFAULT_MAX_ROUNDS, DEFAULT_THRESHOLD, can_accept_winner

_ACTIVE = "_active.json"


def _converge_dir(root: Path) -> Path:
    return Path(root) / ".memory-art" / "converge"


def _read_active(root: Path) -> dict[str, Any]:
    path = _converge_dir(root) / _ACTIVE
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _write_active(root: Path, data: dict[str, Any]) -> None:
    folder = _converge_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / _ACTIVE).write_text(
        json.dumps(data, ensure_ascii=False),
        encoding="utf-8",
    )


def mark_active_session(
    root: Path,
    session_id: str,
    conversation_id: str = "",
) -> None:
    """Mark the converge cell that stop-hook may nudge — keep prior owner when possible."""
    sid = (session_id or "latest").strip() or "latest"
    prev = _read_active(root)
    payload: dict[str, Any] = {"session_id": sid}
    explicit = (conversation_id or "").strip()
    prev_sid = str(prev.get("session_id") or "").strip()
    # Same cell (or first write): keep prior owner; switching to a different sid clears it.
    same_cell = prev_sid in ("", sid) or (prev_sid == "latest" and sid == "latest")
    if explicit:
        payload["owner_conversation_id"] = explicit
    elif same_cell:
        kept = str(prev.get("owner_conversation_id") or "").strip()
        if kept:
            payload["owner_conversation_id"] = kept
    _write_active(root, payload)


def claim_active_conversation(root: Path, conversation_id: str) -> str:
    """Bind active converge to this composer when unbound; return owner id (may be empty)."""
    cid = (conversation_id or "").strip()
    if not cid:
        return ""
    data = _read_active(root)
    if not data.get("session_id"):
        return ""
    owner = str(data.get("owner_conversation_id") or "").strip()
    if not owner:
        data["owner_conversation_id"] = cid
        _write_active(root, data)
        return cid
    return owner


def active_owner_conversation_id(root: Path) -> str:
    return str(_read_active(root).get("owner_conversation_id") or "").strip()


def followup_allowed_for_conversation(root: Path, conversation_id: str) -> bool:
    """
    Only the owning composer may receive stop followup_message.

    - No conversation_id in hook payload → allow (CLI / older hosts).
    - Owner empty → deny for Cursor chats (must claim via GenerateImage pre-gen first).
    - Owner mismatch → deny (do not hijack unrelated chats).
    """
    cid = (conversation_id or "").strip()
    if not cid:
        return True
    owner = active_owner_conversation_id(root)
    if not owner:
        return False
    return owner == cid


def clear_active_session(root: Path, session_id: str = "") -> None:
    path = _converge_dir(root) / _ACTIVE
    if not path.is_file():
        return
    if session_id:
        try:
            current = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            current = {}
        if str(current.get("session_id") or "") not in ("", session_id, "latest"):
            return
    try:
        path.unlink()
    except OSError:
        pass


def load_session(root: Path, session_id: str) -> dict[str, Any]:
    path = _converge_dir(root) / f"{session_id}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def active_session_id(root: Path) -> str:
    return str(_read_active(root).get("session_id") or "").strip()


def loop_followup(root: Path, session_id: str = "") -> dict[str, str] | None:
    """If the active converge cell is not done, return the next mandatory step."""
    sid = (session_id or active_session_id(root) or "").strip()
    if not sid:
        return None
    sess = load_session(root, sid)
    if not sess:
        return None
    if str(sess.get("status") or "") == "finished":
        return None
    rounds = list(sess.get("rounds") or [])
    if not rounds:
        return None
    pending = [
        r for r in rounds
        if not r.get("judged") and str(r.get("image") or "").strip()
    ]
    if pending:
        row = pending[-1]
        rno = int(row.get("round") or 0)
        image = str(row.get("image") or "")
        return {
            "reason": "pending_judge",
            "session_id": sid,
            "message": (
                f"第 {rno} 轮还没审图，不能停。先看图打六维，再运行："
                f"`python pmem_art.py converge judge --id {sid} --round {rno} "
                f"--image \"{image}\" --dims \"构图x/光影x/透视x/质感x/风格x/无瑕疵x\" "
                f"--defects \"...\" --next-fix \"...\"`"
            ),
        }
    judged = [r for r in rounds if r.get("judged") and r.get("score") is not None]
    if not judged:
        return None
    try:
        best = max(float(r.get("score")) for r in judged)
    except (TypeError, ValueError):
        best = 0.0
    n_judged = len(judged)
    th = float(sess.get("accept_threshold") or sess.get("threshold") or DEFAULT_THRESHOLD)
    mr = int(sess.get("max_rounds") or DEFAULT_MAX_ROUNDS)
    if can_accept_winner(n_judged, best, threshold=th, max_rounds=mr):
        return {
            "reason": "need_finish",
            "session_id": sid,
            "message": (
                f"这一格可以结算了。运行 `python pmem_art.py converge finish --id {sid}`，"
                "不要把未审或未满轮的 r1 当成终稿。"
            ),
        }
    nxt = n_judged + 1
    return {
        "reason": "need_next_round",
        "session_id": sid,
        "message": (
            f"第 {n_judged} 轮 {best:.2f} < {th:.2f}，未满 {mr} 轮，不能停。"
            f"必须再出第 {nxt} 轮：GenerateImage → "
            f"`python pmem_art.py converge generate --id {sid} --round {nxt} --image <path> --prompt \"...\"` "
            f"→ `python pmem_art.py converge judge --id {sid} --round {nxt} --image <path> --dims ...`。"
        ),
    }
