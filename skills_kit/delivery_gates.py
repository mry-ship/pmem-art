"""出图交件闸：过线只认 ≥9.5；整表硬伤、写实回落、点名锁在这里卡住。"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .local_locks import lock_prompt_line, locks_from_session, unresolved_named_locks
from .merge_relation import audit_overview_sheet, merge_surface_lock_line, player_named_style

_PHOTO_DEFECT = (
    "写实",
    "摄影",
    "毛发",
    "静物",
    "产品实拍",
    "油光",
    "棚拍",
    "折射",
    "木纹",
    "乳浊",
    "微距",
)
_GRID = re.compile(r"(\d+)\s*[x×]\s*(\d+)")


def is_delivery_pass(score: float, threshold: float = 9.5) -> bool:
    """全技能同一把尺子。8.5、9.0 都不是通过。"""
    return float(score) >= float(threshold)


def generate_prefix(sess: dict[str, Any], prompt: str) -> str:
    """生成词最前面补上 Gossip Harbor 货柜锁和点名锁。"""
    goal = str(sess.get("goal") or "")
    bits: list[str] = []
    if _is_merge(sess):
        # 点名只看 goal；完整硬句才看 prompt（勿把 Warm-Start「避开赛博」当点名）
        line = merge_surface_lock_line(goal=goal, prompt=prompt)
        if line:
            bits.append(line)
    lock_line = lock_prompt_line(locks_from_session(sess))
    if lock_line and lock_line not in (prompt or ""):
        bits.append(lock_line)
    if not bits:
        return prompt
    head = " | ".join(bits)
    if head in (prompt or ""):
        return prompt
    return f"{head} | {prompt}".strip(" |")


def judge_gate_notes(
    sess: dict[str, Any],
    *,
    image: str = "",
    defects: str = "",
    strengths: str = "",
    root: Path | None = None,
) -> list[str]:
    notes: list[str] = []
    goal = str(sess.get("goal") or "")
    if _is_merge(sess) and not player_named_style(goal):
        if any(word in (defects or "") for word in _PHOTO_DEFECT):
            notes.append("未指定风格却偏写实，本轮不能过线；改回 Gossip Harbor 货柜气质")
    hard, _soft = _overview_audit(sess, image=image, root=root)
    if hard:
        notes.extend(hard[:6])
    open_locks = unresolved_named_locks(locks_from_session(sess), defects, strengths)
    if open_locks:
        notes.append("点名锁未单独验收：" + "；".join(open_locks))
    return notes


def overview_sheet_hints(
    sess: dict[str, Any],
    *,
    image: str = "",
    root: Path | None = None,
) -> list[str]:
    """体量软提示：不拦过线，只给 agent 看见。"""
    _hard, soft = _overview_audit(sess, image=image, root=root)
    return soft[:4]


def _overview_audit(
    sess: dict[str, Any],
    *,
    image: str = "",
    root: Path | None = None,
) -> tuple[list[str], list[str]]:
    if sess.get("merge_delivery") != "overview_sheet" or not image:
        return [], []
    path = Path(image)
    if root is not None and not path.is_file():
        path = Path(root) / image
    rows, cols = _grid(str(sess.get("goal") or ""))
    _ok, issues = audit_overview_sheet(path, rows=rows, cols=cols)
    hard = [item for item in issues if not str(item).startswith("提示：")]
    soft = [item for item in issues if str(item).startswith("提示：")]
    return hard, soft


def _is_merge(sess: dict[str, Any]) -> bool:
    ids = [str(x) for x in (sess.get("route_ids") or [])]
    return "merge.ladder" in ids or bool(sess.get("merge_delivery"))


def _grid(goal: str) -> tuple[int, int]:
    match = _GRID.search(goal or "")
    if match:
        return int(match.group(1)), int(match.group(2))
    return 2, 4
