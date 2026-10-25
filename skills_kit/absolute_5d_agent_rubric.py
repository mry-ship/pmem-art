"""Absolute-5D checklist for the *current* multimodal Agent (no independent VLM key).

Pixel offline scorer (`scripts/absolute_5d_scorer.py`) is advisory only.
Without an API key, the Agent that can see the image scores against this rubric.
Converge threshold stays DEFAULT_THRESHOLD (9.6): hit STOP or run max_rounds → best-of-N.
"""
from __future__ import annotations

from .prompt_scale import DEFAULT_THRESHOLD

AGENT_JUDGE_SOURCE = "agent_absolute_5d"

# Compact gpt-6-sol Absolute-5D bands (full text: docs/gpt6sol_absolute_5d_quant_rubric.md)
_BANDS = "档位锚：3=失败 / 5=差 / 7=合格 / 8.5=近优 / 9.5=优（可到 10）"


def agent_absolute_5d_judge_prompt(
    *,
    goal: str = "",
    target_threshold: float = DEFAULT_THRESHOLD,
    round_num: int = 1,
    max_rounds: int = 8,
) -> str:
    """Prompt the current vision-capable model to score one plate Absolute-5D."""
    goal_line = f"目标：{goal.strip()}\n" if goal and goal.strip() else ""
    return (
        f"{goal_line}"
        f"你是独立主美裁判（本会话模型看图评分，非像素启发式）。"
        f"对附图做 Absolute-5D 盲评（忽略生成档位话术，只看画面）。\n"
        f"{_BANDS}\n"
        "五维（各 0–10，一位小数）：构图 composition / 光影 lighting_color / "
        "透视解剖 perspective_anatomy / 质感 texture_detail / 风格规格 spec_style。\n"
        "打分时心里过检查项（每项 0/1/2 再合成维分）：主体可读、层次、光向一致、色偏、"
        "透视/比例、关节、材质可辨、噪点糊边、风格锚点、禁用词规避；看不清就保守给分并写进缺陷。\n"
        f"合格线 ≥{float(target_threshold):.2f}；本轮 {int(round_num)}/{int(max_rounds)}。"
        f"未达标则继续改；满轮后取最高分收工（best-of-N），禁止另设无 Key 低门槛早停。\n"
        "必须输出：\n"
        "1) dims 一行：`构图x.x/光影x.x/透视x.x/质感x.x/风格x.x`\n"
        "2) defects：至少一条可核验画面问题（禁「无明显硬伤」套话）\n"
        "3) strengths：1–2 条\n"
        "4) next_fix：下一轮可执行叠加修正（已达标可写「已达标」）\n"
    )


def annotate_advisory_offline(offline_score: float | None, coverage: float | None) -> str:
    """Short note: heuristic offline is旁证, not the gate."""
    if offline_score is None:
        return "像素离线检查项旁证不可用"
    cov = f"，coverage={coverage}" if coverage is not None else ""
    return (
        f"像素离线 Absolute-5D 旁证={float(offline_score):.2f}{cov}"
        f"（仅参考，不改门槛、不替代本模型五维分）"
    )
