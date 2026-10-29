"""Showcase HTML finish gate.

A scored cell cannot be a final if last score < 9.6 and rounds < 4.
Style-lock / prompt / refs do not generate, so they are skipped.
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from typing import Any

DEFAULT_THRESHOLD = 9.6
DEFAULT_MAX_ROUNDS = 4

_SKIP_CAPTION = re.compile(
    r"^(原图|风格参考|样张|锁定卡|不生图|身份参考|参考)\b"
)
_DROP_SECTIONS = ("prompt", "style")
_ROUND_RE = re.compile(r"(\d+)\s*轮")
_SCORE_RE = re.compile(r"(\d+\.\d{2})")
_SCORE_RUN_RE = re.compile(r"\d+\.\d{2}(?:\s*→\s*\d+\.\d{2})+")


def can_accept_winner(
    rounds: int | None,
    score: float | None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
) -> bool:
    """True when a scored cell may be published as the page winner."""
    if score is None:
        return True
    if float(score) >= float(threshold):
        return True
    if rounds is not None and int(rounds) >= int(max_rounds):
        return True
    return False


def last_score(caption: str) -> float | None:
    hits = _SCORE_RE.findall(caption or "")
    if not hits:
        return None
    return float(hits[-1])


def round_count(caption: str) -> int | None:
    """Completed rounds for this cell. Ignore「前 N 轮作废」history."""
    text = caption or ""
    explicit: list[int] = []
    for match in _ROUND_RE.finditer(text):
        prefix = text[max(0, match.start() - 4):match.start()]
        # 「前 4 轮作废」「胜出第 3 轮」「第 1 轮最高」都不是完成轮次。
        if "前" in prefix or "第" in prefix:
            continue
        explicit.append(int(match.group(1)))
    if explicit:
        return explicit[-1]
    if "本张" in text:
        return 1
    run = _SCORE_RUN_RE.search(text)
    if run:
        parts = _SCORE_RE.findall(run.group(0))
        if len(parts) >= 2:
            return len(parts)
    return None


def _strip_sections(html: str) -> str:
    text = html
    for sid in _DROP_SECTIONS:
        text = re.sub(
            rf'<section id="{sid}">.*?</section>',
            "",
            text,
            flags=re.S | re.I,
        )
    return text


def _plain_caption(raw: str) -> str:
    return unescape(re.sub(r"<[^>]+>", " ", raw or "")).strip()


def audit_showcase_html(html: str) -> list[dict[str, Any]]:
    """Return incomplete scored cells. Empty list means the page may ship."""
    body = _strip_sections(html)
    issues: list[dict[str, Any]] = []
    for match in re.finditer(r"<figcaption>(.*?)</figcaption>", body, flags=re.S | re.I):
        caption = _plain_caption(match.group(1))
        if not caption or _SKIP_CAPTION.search(caption):
            continue
        if "未出图" in caption:
            issues.append(
                {
                    "caption": caption[:160],
                    "rounds": round_count(caption),
                    "score": last_score(caption),
                    "reason": "missing_image",
                }
            )
            continue
        score = last_score(caption)
        if score is None:
            continue
        rounds = round_count(caption)
        if can_accept_winner(rounds, score):
            continue
        issues.append(
            {
                "caption": caption[:160],
                "rounds": rounds,
                "score": score,
                "reason": "under_threshold_before_max_rounds",
            }
        )
    return issues


def audit_showcase_file(path: str | Path) -> list[dict[str, Any]]:
    html = Path(path).read_text(encoding="utf-8")
    return audit_showcase_html(html)


def format_report(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "showcase-gate OK：没有 <9.6 且未满 4 轮的终稿格。"
    lines = [f"showcase-gate FAIL：{len(issues)} 格还不能当终稿"]
    for item in issues:
        lines.append(
            f"- [{item.get('reason')}] rounds={item.get('rounds')} "
            f"score={item.get('score')} {item.get('caption')}"
        )
    return "\n".join(lines)
