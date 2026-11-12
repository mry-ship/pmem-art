"""未点名接续时，禁止把仓库旧任务交付路径当成本趟底稿。"""
from __future__ import annotations

import re
from typing import Iterable

# 玩家显式接续才放行旧案路径
_CONTINUE = re.compile(
    r"接着上次|继续这张|继续上次|接着上轮|用这份|复用旧|旧关系稿|旧目录|"
    r"点名接续|沿用上[次轮]|沿用这份|接着做这[张份]",
    re.I,
)

# 旧任务交付痕迹（不含 assets/refs、downloads、suite/refs 参考垫图）
_PRIOR_DELIVERABLE = re.compile(
    r"(?:^|[/\\])assets[/\\]skill_[^/\\]+|"
    r"sheet_session_|"
    r"sheet_r\d+|"
    r"merge_phase1\.ya?ml|"
    r"(?:^|[/\\])relation\.md$|"
    r"\.memory-art[/\\]converge[/\\]|"
    r"CHAT\d{6,}(?:RECIPE|REDLINE)",
    re.I,
)

# 明确参考垫图：允许在 skill_* 清点目录的 refs/ 下，或 downloads / assets/refs
_REF_PAD_ALLOW = re.compile(
    r"(?:^|[/\\])(?:assets[/\\]refs[/\\]|downloads[/\\]|下载[/\\])|"
    r"(?:^|[/\\])assets[/\\]skill_[^/\\]+[/\\]refs[/\\]",
    re.I,
)


def _is_allowed_ref_pad(path: str) -> bool:
    p = (path or "").replace("\\", "/")
    if not p:
        return False
    if _REF_PAD_ALLOW.search(p):
        return True
    # suite 清点 refs 的别名：…/skill_YYYYMMDD_suite/refs/…
    if re.search(r"/assets/skill_\d{8}_[^/]+/refs/", p, re.I):
        return True
    return False


def assert_no_silent_prior_asset_reuse(
    goal: str = "",
    paths: Iterable[str] | None = None,
) -> tuple[bool, str]:
    """Reject start/generate when goal/refs point at prior task deliverables without continue words.

    Allows assets/refs/*、downloads/*、assets/skill_*/refs/* layout/style pads.
    Blocks assets/skill_* 交付（out/sheet/phase1）与 converge 板。
    """
    goal_text = str(goal or "")
    if _CONTINUE.search(goal_text):
        return True, ""
    hits: list[str] = []
    for raw in list(paths or []):
        p = str(raw or "").strip().replace("\\", "/")
        if not p:
            continue
        if _is_allowed_ref_pad(p):
            continue
        if _PRIOR_DELIVERABLE.search(p):
            hits.append(p)
    # goal 里直接写了旧交付路径（refs 垫图放行）
    for m in re.finditer(
        r"(?:assets[/\\]skill_[^\s\"']+|sheet_session_[^\s\"']+|sheet_r\d+[^\s\"']*|"
        r"merge_phase1\.ya?ml|\.memory-art[/\\]converge[/\\][^\s\"']+|"
        r"CHAT\d{6,}(?:RECIPE|REDLINE))",
        goal_text,
        re.I,
    ):
        tok = m.group(0).replace("\\", "/")
        if _is_allowed_ref_pad(tok):
            continue
        hits.append(m.group(0))
    if not hits:
        return True, ""
    shown = "；".join(dict.fromkeys(hits))
    return (
        False,
        "未点名接续却引用仓库旧任务交付路径（"
        f"{shown}）。请新开关系稿/目录；若确要续旧案，在 goal 写明「接着上次/用这份稿」。",
    )


_STYLE_DRIFT = re.compile(
    r"写实|产品静物|美食棚拍|摄影感|玻璃真实折射|硬3D写实|棚拍产品|果汁乳浊|"
    r"光泽卡通\s*3D|硬卡通\s*CGI|硬镜面\s*CGI|平面绘本贴纸|哑光黏土拟态",
)


def prior_rounds_show_style_drift(rounds: list[dict] | None, round_num: int) -> bool:
    """True when earlier judged rounds already named photoreal / product-still drift."""
    for row in rounds or []:
        if not isinstance(row, dict):
            continue
        try:
            rno = int(row.get("round") or 0)
        except (TypeError, ValueError):
            continue
        if rno >= int(round_num):
            continue
        blob = f"{row.get('defects') or ''} {row.get('next_fix') or ''}"
        if _STYLE_DRIFT.search(blob):
            return True
    return False
