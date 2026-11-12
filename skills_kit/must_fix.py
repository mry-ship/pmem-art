"""下一轮改点：压成 ≤2 条短约束，稳定注入 generate 提示词。

只做加法：不改 scale / 阈值 / 路由；原 prompt 仍保留。
续写前先剥掉会换题材/换品类/换技能的 L0 换轨句，避免 MUST_FIX 把方向带走。
"""
from __future__ import annotations

import re
from typing import Iterable

# 改点里夹带「换题材/换画风/换技能/推倒重来」→ 续写层不许带进 generate
_DIRECTION_SWAP = re.compile(
    r"(?:换成|改成|换做|做成|改画成|整张改成).{0,16}(?:题材|画风|风格|品类|交付|物种)|"
    r"(?:推倒重来|另起炉灶|从零再做|换条路|换个思路|换方案|历史作废|全部作废)|"
    r"(?:改走|改成|不要走|别走).{0,10}(?:合成梯|界面|图标|克隆|变体|普通图|镜头包)|"
    r"(?:换一条|换个).{0,8}(?:技能|合同|路由)",
    re.I,
)


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


def sanitize_continuation_fix(text: str) -> str:
    """Drop L0 direction-swap clauses from judge next_fix before R2+ inject."""
    kept: list[str] = []
    for item in _split_items(text):
        if _DIRECTION_SWAP.search(item):
            continue
        kept.append(item)
    return "；".join(kept).strip()


def clip_must_fix(text: str, *, max_items: int = 2, max_chars: int = 200) -> str:
    """Keep at most max_items actionable fixes; trim total length."""
    cleaned = sanitize_continuation_fix(text)
    items = _split_items(cleaned)[: max(1, int(max_items))] if cleaned else []
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
