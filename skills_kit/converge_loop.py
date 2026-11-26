"""Force the generate → judge → next-round loop without relying on agent memory."""
from __future__ import annotations

from .platform_cli import pmem_art_cli
import json
from pathlib import Path
from typing import Any

from .converge_policy import EARLY_STOP_REASONS
from .showcase_gate import DEFAULT_MAX_ROUNDS, DEFAULT_THRESHOLD, can_accept_winner

_ACTIVE = "_active.json"


from core.session import converge_dir as _converge_dir, session_json_path  # noqa: F401


def _empty_index() -> dict[str, Any]:
    return {"sessions": {}, "conversations": {}, "order": []}


def _normalize_active(data: dict[str, Any]) -> dict[str, Any]:
    """Accept the old single pointer and the session/conversation index."""
    if not isinstance(data, dict):
        return _empty_index()
    sessions = data.get("sessions")
    if isinstance(sessions, dict):
        clean: dict[str, Any] = {}
        for sid, entry in sessions.items():
            key = str(sid or "").strip()
            if not key:
                continue
            if isinstance(entry, dict):
                clean[key] = {
                    "conversation_id": str(entry.get("conversation_id") or "").strip(),
                    "started_at": str(entry.get("started_at") or "").strip(),
                }
            else:
                clean[key] = {
                    "conversation_id": str(entry or "").strip(),
                    "started_at": "",
                }
        convs_in = data.get("conversations")
        convs: dict[str, str] = {}
        if isinstance(convs_in, dict):
            for cid, sid in convs_in.items():
                c = str(cid or "").strip()
                s = str(sid or "").strip()
                if c and s in clean and clean[s]["conversation_id"] == c:
                    convs[c] = s
        for sid, entry in clean.items():
            cid = entry["conversation_id"]
            if cid and cid not in convs:
                convs[cid] = sid
        order = [str(x) for x in (data.get("order") or []) if str(x) in clean]
        for sid in clean:
            if sid not in order:
                order.append(sid)
        return {"sessions": clean, "conversations": convs, "order": order}
    sid = str(data.get("session_id") or "").strip()
    if not sid:
        return _empty_index()
    owner = str(data.get("owner_conversation_id") or "").strip()
    convs = {owner: sid} if owner else {}
    return {
        "sessions": {sid: {"conversation_id": owner, "started_at": ""}},
        "conversations": convs,
        "order": [sid],
    }


def _read_active(root: Path) -> dict[str, Any]:
    path = _converge_dir(root) / _ACTIVE
    if not path.is_file():
        return _empty_index()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_index()
    return _normalize_active(data if isinstance(data, dict) else {})


def _write_active(root: Path, data: dict[str, Any]) -> None:
    folder = _converge_dir(root)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / _ACTIVE).write_text(
        json.dumps(_normalize_active(data), ensure_ascii=False),
        encoding="utf-8",
    )


def mark_active_session(
    root: Path,
    session_id: str,
    conversation_id: str = "",
    started_at: str = "",
) -> None:
    """Register one session. A later session must not erase another session's owner."""
    sid = (session_id or "latest").strip() or "latest"
    data = _read_active(root)
    sessions: dict[str, Any] = data["sessions"]
    convs: dict[str, str] = data["conversations"]
    entry = dict(sessions.get(sid) or {"conversation_id": "", "started_at": ""})
    if (started_at or "").strip():
        entry["started_at"] = started_at.strip()
    explicit = (conversation_id or "").strip()
    if explicit:
        previous = str(entry.get("conversation_id") or "").strip()
        if previous and previous != explicit and convs.get(previous) == sid:
            convs.pop(previous, None)
        other = convs.get(explicit)
        if other and other != sid:
            other_entry = dict(sessions.get(other) or {"conversation_id": ""})
            if other_entry.get("conversation_id") == explicit:
                other_entry["conversation_id"] = ""
                sessions[other] = other_entry
        entry["conversation_id"] = explicit
        convs[explicit] = sid
    sessions[sid] = entry
    order = [x for x in data["order"] if x != sid]
    order.append(sid)
    _write_active(root, {"sessions": sessions, "conversations": convs, "order": order})


def claim_active_conversation(
    root: Path,
    conversation_id: str,
    session_id: str = "",
) -> str:
    """Bind this conversation to one unbound session. Never steal another owner."""
    cid = (conversation_id or "").strip()
    if not cid:
        return ""
    data = _read_active(root)
    sessions: dict[str, Any] = data["sessions"]
    convs: dict[str, str] = data["conversations"]
    if not sessions:
        return ""
    bound = convs.get(cid)
    if bound and bound in sessions:
        return str(sessions[bound].get("conversation_id") or "")
    requested = (session_id or "").strip()
    if requested:
        targets = [requested] if requested in sessions else []
    else:
        targets = [
            sid
            for sid, entry in sessions.items()
            if not str(entry.get("conversation_id") or "").strip()
        ]
    if len(targets) != 1:
        return ""
    sid = targets[0]
    entry = dict(sessions.get(sid) or {"conversation_id": ""})
    owner = str(entry.get("conversation_id") or "").strip()
    if owner and owner != cid:
        return owner
    entry["conversation_id"] = cid
    sessions[sid] = entry
    convs[cid] = sid
    _write_active(
        root,
        {"sessions": sessions, "conversations": convs, "order": data["order"]},
    )
    return cid


def active_owner_conversation_id(root: Path, session_id: str = "") -> str:
    data = _read_active(root)
    sid = (session_id or "").strip()
    sessions: dict[str, Any] = data["sessions"]
    if not sid:
        if len(sessions) != 1:
            return ""
        sid = next(iter(sessions))
    entry = sessions.get(sid) or {}
    return str(entry.get("conversation_id") or "").strip()


def followup_allowed_for_conversation(root: Path, conversation_id: str) -> bool:
    """
    Only the composer that owns a registered session may receive stop followup.

    - No conversation_id in hook payload → allow (CLI / older hosts).
    - This conversation is not in the index → deny (must claim via GenerateImage
      post-asset; pre-gen never claims).
    - Another conversation's session does not make this one allowed.
    """
    cid = (conversation_id or "").strip()
    if not cid:
        return True
    data = _read_active(root)
    sid = str(data["conversations"].get(cid) or "").strip()
    if not sid:
        return False
    entry = data["sessions"].get(sid) or {}
    return str(entry.get("conversation_id") or "").strip() == cid


def clear_active_session(
    root: Path,
    session_id: str = "",
    started_at: str = "",
) -> None:
    path = _converge_dir(root) / _ACTIVE
    if not path.is_file():
        return
    if not (session_id or "").strip():
        try:
            path.unlink()
        except OSError:
            pass
        return
    data = _read_active(root)
    sid = session_id.strip()
    sessions: dict[str, Any] = data["sessions"]
    if sid not in sessions:
        return
    entry = sessions[sid]
    expected = (started_at or "").strip()
    recorded = str(entry.get("started_at") or "").strip()
    if expected and recorded and expected != recorded:
        return
    sessions.pop(sid)
    convs: dict[str, str] = data["conversations"]
    cid = str(entry.get("conversation_id") or "").strip()
    if cid and convs.get(cid) == sid:
        convs.pop(cid, None)
    order = [x for x in data["order"] if x != sid]
    if not sessions:
        try:
            path.unlink()
        except OSError:
            pass
        return
    _write_active(root, {"sessions": sessions, "conversations": convs, "order": order})


def load_session(root: Path, session_id: str) -> dict[str, Any]:
    path = session_json_path(root, session_id)
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def active_session_id(root: Path, conversation_id: str = "") -> str:
    """Session for this conversation. With no conversation, only when exactly one is registered."""
    data = _read_active(root)
    cid = (conversation_id or "").strip()
    if cid:
        return str(data["conversations"].get(cid) or "").strip()
    sessions: dict[str, Any] = data["sessions"]
    if len(sessions) == 1:
        return next(iter(sessions))
    return ""


def loop_followup(
    root: Path,
    session_id: str = "",
    conversation_id: str = "",
) -> dict[str, str] | None:
    """Next step for one session. A conversation resolves its own session, not the latest start."""
    sid = (session_id or "").strip()
    if not sid and (conversation_id or "").strip():
        sid = active_session_id(root, conversation_id=conversation_id)
    if not sid:
        sid = active_session_id(root)
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
        from .understanding_contract import working_set_from_session

        ws = working_set_from_session(sess, session_id=sid)
        return {
            "reason": "pending_judge",
            "session_id": sid,
            "message": (
                f"第 {rno} 轮还没审图，不能停。先看图打六维，再运行："
                f"`{pmem_art_cli()} converge judge --id {sid} --round {rno} "
                f"--image \"{image}\" --dims \"构图x/光影x/透视x/质感x/风格x/无瑕疵x\" "
                f"--defects \"...\" --next-fix \"...\"`\n{ws}"
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
    early_flag = str(sess.get("status") or "") == "early_safe_stop" or any(
        str(r.get("decision") or "") in EARLY_STOP_REASONS
        or str(r.get("early_safe_stop") or "") in EARLY_STOP_REASONS
        for r in judged
    )
    if can_accept_winner(
        n_judged, best, threshold=th, max_rounds=mr, early_safe_stop=early_flag
    ):
        return {
            "reason": "need_finish",
            "session_id": sid,
            "message": (
                f"这一格可以结算了。运行 `{pmem_art_cli()} converge finish --id {sid}`，"
                "不要把未审或未满轮的 r1 当成终稿。"
            ),
        }
    nxt = n_judged + 1
    from .understanding_contract import working_set_from_session

    ws = working_set_from_session(sess, session_id=sid)
    return {
        "reason": "need_next_round",
        "session_id": sid,
        "message": (
            f"第 {n_judged} 轮 {best:.2f} < {th:.2f}，未满 {mr} 轮，不能停。"
            f"必须再出第 {nxt} 轮：GenerateImage → "
            f"`{pmem_art_cli()} converge generate --id {sid} --round {nxt} --image <path> --prompt \"...\"` "
            f"→ `{pmem_art_cli()} converge judge --id {sid} --round {nxt} --image <path> --dims ...`。\n"
            f"先读最小工作集（勿重谈合同）：`{pmem_art_cli()} contract working-set --id {sid}`\n{ws}"
        ),
    }
