"""Converge session file locations. Pure path logic, no product imports."""
from __future__ import annotations

from pathlib import Path


def converge_dir(root: Path) -> Path:
    return Path(root) / ".memory-art" / "converge"


def session_json_path(root: Path, session_id: str, *, suffix: str = ".json") -> Path | None:
    """会话文件必须落在 .memory-art/converge 这一层。拒绝 .. 和分隔符。"""
    folder = converge_dir(root).resolve()
    sid = (session_id or "").strip()
    if not sid or any(ch in sid for ch in "/\\:\0"):
        return None
    path = (folder / f"{sid}{suffix}").resolve()
    if path.parent != folder:
        return None
    return path
