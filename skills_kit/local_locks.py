"""点名部位锁：每轮生成都带上，审图必须单独验收。"""
from __future__ import annotations

from typing import Any

# 长词在前，避免「眼睛」再被「眼」拆一次。
_PARTS = (
    "眼睛",
    "手指",
    "信纸",
    "蝴蝶结",
    "树屋",
    "池塘",
    "提梁",
    "翅膀",
    "嘴",
    "眼",
    "手",
    "脚",
)


def _parts_in(text: str) -> list[str]:
    found: list[str] = []
    rest = text or ""
    if "手机" in rest and "手指" not in rest:
        rest = rest.replace("手机", "")
    for part in _PARTS:
        if part in rest:
            found.append(part)
            rest = rest.replace(part, "")
    return found


def locks_from_session(sess: dict[str, Any] | None) -> list[str]:
    uc = (sess or {}).get("understanding_contract") or {}
    l1 = uc.get("l1") if isinstance(uc.get("l1"), dict) else {}
    locks = [str(x).strip() for x in (l1.get("locks") or []) if str(x).strip()]
    goal = str((sess or {}).get("goal") or "")
    for part in _parts_in(goal):
        if not any(part in lock for lock in locks):
            locks.append(part)
    return locks


def lock_prompt_line(locks: list[str]) -> str:
    if not locks:
        return ""
    return "点名锁每轮都要单独留住，不许整张漂掉：" + "；".join(locks)


def unresolved_named_locks(
    locks: list[str],
    defects: str = "",
    strengths: str = "",
) -> list[str]:
    """点名部位仍在缺陷里，或优点没单独写明守住，都算没验收。"""
    defects = defects or ""
    strengths = strengths or ""
    open_locks: list[str] = []
    for lock in locks:
        parts = _parts_in(lock) or ([lock] if len(lock) <= 16 else [])
        if not parts:
            continue
        for part in parts:
            if part in defects or part not in strengths:
                open_locks.append(lock)
                break
    return open_locks
