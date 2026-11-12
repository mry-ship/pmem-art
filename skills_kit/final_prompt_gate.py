"""出图必须用 converge generate 打印的最终 Prompt；禁止另写/手贴。"""
from __future__ import annotations

import hashlib
import re


_FINAL_MARK = "最终 Prompt（出图须用这句）"
_HAND_PASTE_MARKS = (
    "【Warm-Start 注入包",
    "优先复用定稿方向",
    "手贴 Warm-Start",
)


def final_prompt_sha1(prompt: str) -> str:
    text = str(prompt or "").strip().encode("utf-8")
    return hashlib.sha1(text).hexdigest()[:12] if text else ""


def format_final_prompt_lines(prompt: str) -> list[str]:
    """Machine-checkable lines for Agent / tests after generate."""
    body = str(prompt or "").strip()
    sha = final_prompt_sha1(body)
    return [
        f"FINAL_PROMPT_SHA1={sha or '-'}",
        f"   · {_FINAL_MARK}: {body}",
        "   · 出图硬规：GenerateImage/外部 API 的 description 必须逐字用上面这句；"
        "禁止另写 brief、禁止手贴 Warm-Start、禁止只贴装配句。",
    ]


def assert_used_final_prompt(used: str, expected: str) -> tuple[bool, str]:
    """Compare what the agent sent to the image tool vs generate's final prompt."""
    u = str(used or "").strip()
    e = str(expected or "").strip()
    if not e:
        return False, "会话没有最终 Prompt；请先跑 converge generate"
    if not u:
        return False, "生图 description 为空；必须粘贴最终 Prompt"
    if u == e:
        return True, ""
    if final_prompt_sha1(u) == final_prompt_sha1(e):
        return True, ""
    # Allow tool wrappers that prepend engine tags but keep body
    if e in u and not any(m in u and m not in e for m in _HAND_PASTE_MARKS if m not in e):
        # body contained; still reject if agent re-pasted warm-start on top of a short brief
        if len(u) <= len(e) + 80:
            return True, ""
    return (
        False,
        f"生图词与最终 Prompt 不一致（期望 sha1={final_prompt_sha1(e)}，实际 sha1={final_prompt_sha1(u)}）。"
        "请勿另写 brief。",
    )


def looks_like_hand_pasted_warm_start(text: str) -> bool:
    """True when Agent appears to have hand-built a Warm-Start paste outside generate."""
    blob = str(text or "")
    if "优先复用定稿方向" in blob:
        return True
    # Warm-Start mark alone is OK if it came from generate merge; detect orphan paste hints
    return bool(re.search(r"手贴\s*Warm-Start|请把下面记忆包贴进提示词", blob, re.I))
