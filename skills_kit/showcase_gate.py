"""Showcase HTML finish gate.

A scored **final** cell cannot ship if last score < 9.5 and completed rounds < 4
(unless early safe-stop). Style-lock / prompt / refs do not generate, so they are skipped.

Process boards (`process_board.py`) caption each history card as「第 N 轮 · score」and mark
the winner with ``figure.card.win``. Intermediate history cards are **not** finals — only
the winner card (or showcase cells like「low · 3 轮」) are gated.
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path
from typing import Any

from .prompt_scale import DEFAULT_MAX_ROUNDS, DEFAULT_THRESHOLD

_SKIP_CAPTION = re.compile(
    r"^(原图|风格参考|样张|锁定卡|不生图|身份参考|参考|图\d+)\b"
)
_DROP_SECTIONS = ("prompt", "style")
_ROUND_RE = re.compile(r"(\d+)\s*轮")
_PROCESS_ROUND_RE = re.compile(r"^第\s*(\d+)\s*轮\b")
_SCORE_RE = re.compile(r"(\d+\.\d{2})")
_SCORE_RUN_RE = re.compile(r"\d+\.\d{2}(?:\s*→\s*\d+\.\d{2})+")


def can_accept_winner(
    rounds: int | None,
    score: float | None,
    *,
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    early_safe_stop: bool = False,
) -> bool:
    """True when a scored cell may be published as the page winner."""
    if score is None:
        return True
    if float(score) >= float(threshold):
        return True
    if rounds is not None and int(rounds) >= int(max_rounds):
        return True
    # finish 在 STOP_REGRESSION / STOP_PLATEAU / 出图一轮交件硬顶后收最高分，允许低于 9.5 入展陈
    if early_safe_stop and rounds is not None and int(rounds) >= 1:
        return True
    return False


def last_score(caption: str) -> float | None:
    hits = _SCORE_RE.findall(caption or "")
    if not hits:
        return None
    return float(hits[-1])


def round_count(caption: str) -> int | None:
    """Completed rounds / process-board round index for this cell.

    - 「第 N 轮 · score」→ N（过程板真实文案；旧逻辑因跳过「第」而解析成 None）
    - 「low · 3 轮」「完成 4 轮」→ 显式完成轮次
    - 「前 N 轮作废」「胜出第 N 轮」单独出现 → 不当完成轮次（后者需另有「M 轮」）
    """
    text = (caption or "").strip()
    if not text:
        return None

    # 过程板单卡：第 N 轮 · 9.22
    m_proc = _PROCESS_ROUND_RE.match(text)
    if m_proc:
        return int(m_proc.group(1))

    explicit: list[int] = []
    for match in _ROUND_RE.finditer(text):
        prefix = text[max(0, match.start() - 4) : match.start()]
        # 「前 4 轮作废」
        if "前" in prefix:
            continue
        # 「胜出第 3 轮」——胜出指针，不是完成轮次计数
        window = text[max(0, match.start() - 6) : match.start()]
        if "胜出" in window:
            continue
        # 「第 1 轮最高」嵌在「4 轮 · 第 1 轮最高」里：跳过嵌套「第」，保留「4 轮」
        if re.search(r"第\s*$", prefix):
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
    """Return incomplete **final** scored cells. Empty list means the page may ship.

    Process-board history cards（非 win 的「第 N 轮」）跳过；只审胜出格与展陈终稿格。
    """
    body = _strip_sections(html)
    issues: list[dict[str, Any]] = []
    # Prefer figure-scoped scan so we can see class="card win"
    figure_iter = list(
        re.finditer(r"<figure([^>]*)>(.*?)</figure>", body, flags=re.S | re.I)
    )
    if figure_iter:
        cells: list[tuple[str, str, str]] = []
        for fig in figure_iter:
            attrs = fig.group(1) or ""
            inner = fig.group(2) or ""
            cap_m = re.search(r"<figcaption>(.*?)</figcaption>", inner, flags=re.S | re.I)
            if not cap_m:
                continue
            cells.append((attrs, _plain_caption(cap_m.group(1)), inner))
    else:
        cells = [
            ("", _plain_caption(m.group(1)), m.group(1))
            for m in re.finditer(r"<figcaption>(.*?)</figcaption>", body, flags=re.S | re.I)
        ]

    # 过程板：胜出卡写的是「第 N 轮」= 胜出轮次号，完成轮次取页上最大「第 M 轮」
    process_cells: list[tuple[str, str, str, int, float | None]] = []
    for attrs, cap, inner in cells:
        m = _PROCESS_ROUND_RE.match(cap or "")
        if not m:
            continue
        process_cells.append((attrs, cap, inner, int(m.group(1)), last_score(cap)))
    max_process_rounds = max((n for *_, n, _sc in process_cells), default=None)
    has_process_win = any(
        re.search(r'(?:^|[\s"\'])win(?:[\s"\']|$)', attrs, flags=re.I)
        for attrs, *_rest in process_cells
    )
    # 无 win（预览板）：只审「最高分」那张；同分取轮次更大的，避免历史低分拖垮整页、也避免无 win 整页误放行
    provisional_key: tuple[float, int] | None = None
    if process_cells and not has_process_win:
        provisional_key = max(
            ((sc if sc is not None else -1.0), n) for *_a, n, sc in process_cells
        )
    page_early = bool(
        re.search(r"(安全早停|出图一轮交件|STOP_REGRESSION|STOP_PLATEAU)", body, re.I)
    )

    for attrs, caption, inner in cells:
        if not caption or _SKIP_CAPTION.search(caption):
            continue
        is_process_round = bool(_PROCESS_ROUND_RE.match(caption))
        is_win = bool(re.search(r'(?:^|[\s"\'])win(?:[\s"\']|$)', attrs, flags=re.I))
        if is_process_round and not is_win:
            if has_process_win:
                # 有胜出格：历史卡跳过
                continue
            # 无胜出格：只审临时最高分卡
            m = _PROCESS_ROUND_RE.match(caption)
            sc = last_score(caption)
            key = (sc if sc is not None else -1.0, int(m.group(1)) if m else 0)
            if provisional_key is None or key != provisional_key:
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
        if is_process_round and max_process_rounds is not None and (
            is_win or not has_process_win
        ):
            rounds = max_process_rounds
        early = bool(
            re.search(
                r"(安全早停|出图一轮交件|STOP_REGRESSION|STOP_PLATEAU)",
                caption + " " + inner,
                re.I,
            )
        )
        if (
            not early
            and page_early
            and is_process_round
            and (is_win or not has_process_win)
        ):
            early = True
        if can_accept_winner(rounds, score, early_safe_stop=early):
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
    html_path = Path(path)
    html = html_path.read_text(encoding="utf-8")
    issues = audit_showcase_html(html)
    # 终稿/展陈页引用的本地图片必须存在（相对 HTML 路径解析）
    for m in re.finditer(r'<img\b[^>]*\bsrc=["\']([^"\']+)["\']', html, flags=re.I):
        src = (m.group(1) or "").strip()
        if not src or src.startswith(("http://", "https://", "data:")):
            continue
        target = (html_path.parent / src).resolve()
        try:
            target.relative_to(html_path.resolve().parents[2] if len(html_path.resolve().parts) > 2 else html_path.resolve().parent)
        except ValueError:
            pass
        if not target.is_file():
            issues.append(
                {
                    "caption": src[:160],
                    "rounds": None,
                    "score": None,
                    "reason": "missing_image_file",
                }
            )
    return issues


def format_report(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return "showcase-gate OK：没有 <9.5 且未满 4 轮的终稿格。"
    lines = [f"showcase-gate FAIL：{len(issues)} 格还不能当终稿"]
    for item in issues:
        lines.append(
            f"- [{item.get('reason')}] rounds={item.get('rounds')} "
            f"score={item.get('score')} {item.get('caption')}"
        )
    return "\n".join(lines)
