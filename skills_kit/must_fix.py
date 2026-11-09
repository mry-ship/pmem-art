"""下一轮改点：压成 ≤2 条短约束，稳定注入 generate 提示词。

只做加法：不改 scale / 阈值 / 路由；原 prompt 仍保留。
"""
from __future__ import annotations

import re
from typing import Iterable


def _split_items(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    # Prefer explicit separators; fall back to clause breaks.
    parts = re.split(r"[；;。\n]+|(?<=[，,])\s*(?=优先|随后|再|并|同时|然后)", raw)
    out: list[str] = []
    for p in parts:
        item = re.sub(r"\s+", " ", (p or "").strip(" 　·—|-"))
        if len(item) < 4:
            continue
        out.append(item)
    if out:
        return out
    return [raw]


def clip_must_fix(text: str, *, max_items: int = 2, max_chars: int = 200) -> str:
    """Keep at most max_items actionable fixes; trim total length."""
    items = _split_items(text)[: max(1, int(max_items))]
    joined = "；".join(items).strip()
    if len(joined) > max_chars:
        joined = joined[: max_chars - 1].rstrip("；;，, ") + "…"
    return joined


def inject_must_fix(prompt: str, fix: str, *, marker: str = "MUST_FIX") -> str:
    """Append clipped fix once; idempotent if marker/fix already present."""
    base = (prompt or "").strip()
    clipped = clip_must_fix(fix)
    if not clipped:
        return base
    if marker in base and clipped[:24] in base:
        return base
    if clipped in base:
        return base
    tag = f"{marker} (≤2): {clipped}"
    if not base:
        return tag
    return f"{base} | {tag}"


def previous_round_next_fix(rounds: Iterable[dict], round_num: int) -> str:
    """Best next_fix from the latest judged round before round_num."""
    prior = [
        r
        for r in (rounds or [])
        if isinstance(r, dict)
        and int(r.get("round") or 0) < int(round_num or 0)
        and str(r.get("next_fix") or "").strip()
    ]
    if not prior:
        return ""
    last = max(prior, key=lambda r: int(r.get("round") or 0))
    return str(last.get("next_fix") or "").strip()
