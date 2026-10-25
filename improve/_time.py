"""Shared CST clock for improve package."""
from __future__ import annotations

from datetime import datetime, timezone, timedelta


def _now_cst() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))
