"""Absolute-5D checklist for the *current* multimodal Agent (no independent VLM key).

The official score is this look-at-the-image pass. Pixel offline scores are not used.
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
    max_rounds: int = 4,
) -> str:
    """Prompt the current vision-capable model to score one plate Absolute-5D."""
    contract = (
        f"合同只用来写 defects（画没画到），禁止因为 Prompt 写过就加分：{goal.strip()}\n"
        if goal and goal.strip()
        else ""
    )
    return (
        f"你是独立主美裁判。先只看附图，不要看生成提示词给自己加分。\n"
        f"{_BANDS}\n"
        "普通完成图应在 7.0～8.5。9.3+ 只给明显优于合格线的画面。"
        "不要因为后面还要迭代就从 9.3 起跳，也不要把六维打成一串几乎相同的 9.3+。"
        "只写各维分数。正式分由程序按加权调和平均计算，门槛维低于线时改取该维。"
        "像素、Q版、平涂、水彩、剪纸、等轴按该媒介自己的尺子打偏低的那一维，断肢和塌缩仍按硬伤。\n"
        "六维（各 0–10，一位小数）：构图 composition / 光影 lighting_color / "
        "透视解剖 perspective_anatomy / 质感 texture_detail / 风格规格 spec_style / "
        "无瑕疵 flawlessness。无瑕疵与另外五维一样盲评，不另写扣分清单。看不清就保守给分并写进缺陷。\n"
        f"{contract}"
        f"停机门槛 ≥{float(target_threshold):.2f} 是停机线，不是「合格=9.6」。"
        f"本轮 {int(round_num)}/{int(max_rounds)}；满轮取最高分（best-of-N）。\n"
        "必须输出：\n"
        "1) dims 一行：`构图x.x/光影x.x/透视x.x/质感x.x/风格x.x/无瑕疵x.x`\n"
        "2) defects：至少一条可核验画面问题（禁「无明显硬伤」套话）。"
        "必须写本张图上看得见的部位，禁止把上一轮 defects 原句贴过来。\n"
        "3) strengths：1–2 条，只写这张图已经有的，不写提示词里的目标。\n"
        "4) next_fix：下一轮可执行叠加修正（已达标可写「已达标」）\n"
        "recompose：defects 第一句必须回答仰还是俯、人占画面大约多少、主光是窗火还是灯笼。"
        "提示词里的「重构机位」不算成图已经换了机位。\n"
        "high：必须写明相对原图多出来的那一处光影或叙事；写不出来就把构图当贴原打。\n"
    )


def annotate_advisory_offline(offline_score: float | None = None, coverage: float | None = None) -> str:
    """Retired. Kept so older callers do not crash; the judge no longer prints a pixel score."""
    del offline_score, coverage
    return ""
