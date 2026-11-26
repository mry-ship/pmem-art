"""Drop warm-start / taste phrases that contradict the current brief. Pure text, no product imports."""
from __future__ import annotations

import re

_CLAUSE_NEG = re.compile(r"(避免|不要|不许|禁止|严禁|勿|别再|别加|别用|别画|别|无)$")
_FILL_ASK = re.compile(
    r"撑满|约占[^。；|\n]{0,8}\d+\s*%|占到\s*\d+\s*%|"
    r"\d+\s*%[^。；|\n]{0,12}安全区|放大到|四边裁|只留在四角"
)
_JUICY_ASK = re.compile(r"高饱和|软卡通厚体积|冷暖相反|冷底暖|与英雄冷暖")
_BLOCK_HL_ASK = re.compile(r"高光成块")
_GLAZE_ASK = re.compile(r"厚糖釉|糖釉")
_SHADOW_ASK = re.compile(
    r"不要[^。；|\n]{0,18}投影|无投影|收掉[^。；|\n]{0,10}投影|"
    r"少留[^。；|\n]{0,10}投影|投影收掉"
)
_HIGH_SAT = re.compile(r"高饱和")
_REJECT_REF_PERSON = re.compile(
    r"不要画国王|不要国王|不要人脸|不要画人脸|不要胡子|不要皇冠"
)


def _clause_affirmed(text: str, pattern: re.Pattern[str]) -> bool:
    """True when a match is a request, not a phrase the same clause tells the model to avoid."""
    for match in pattern.finditer(text or ""):
        window = text[max(0, match.start() - 16) : match.start()]
        for sep in "，,。；;！!\n、：:（）()[]【】|":
            cut = window.rfind(sep)
            if cut >= 0:
                window = window[cut + 1 :]
                break
        if _CLAUSE_NEG.search(window.rstrip("「」\"'“” ")):
            continue
        return True
    return False


def _drop_pref_token(text: str, key: str, token: str) -> str:
    def repl(match: re.Match[str]) -> str:
        parts = [
            part.strip()
            for part in re.split(r"\s*/\s*", match.group(1))
            if part.strip() and part.strip() != token
        ]
        if not parts:
            return ""
        return f"{key}={' / '.join(parts)}"

    return re.sub(rf"{re.escape(key)}=([^；;\n|]+)", repl, text)


def _drop_ban_token(text: str, token: str) -> str:
    """Remove one slash-separated ban, leaving the rest of the habit line."""
    text = text.replace(f"{token}/", "").replace(f"/{token}", "")
    text = re.sub(rf"(?<=[：:])\s*{re.escape(token)}(?=\s*[；;]|$)", "", text)
    return re.sub(r"[；;]{2,}", "；", text)


def drop_opposed_injections(prompt: str, *, memory_block: str = "", brief: str = "") -> str:
    """Current brief wins over taste and scale lines that say the opposite.

    Taste stays in the profile. Only this prompt loses the opposing phrase.
    Pass ``brief`` when ``prompt`` is just the Warm-Start block or the scale
    clause, so those clauses are never added once the brief already disagrees.
    """
    text = str(prompt or "")
    if not text.strip():
        return text
    authored = str(brief or "").strip()
    if authored:
        source = authored
    else:
        source = text
        block = str(memory_block or "").strip()
        if block and block in source:
            source = source.replace(block, " ", 1)
    if _clause_affirmed(source, _JUICY_ASK):
        text = _drop_pref_token(text, "色温", "避免过饱和")
    if _clause_affirmed(source, _GLAZE_ASK):
        text = _drop_ban_token(text, "油腻高光")
    if _clause_affirmed(source, _SHADOW_ASK) or _clause_affirmed(source, _BLOCK_HL_ASK):
        text = _drop_pref_token(text, "光影", "柔光")
        text = re.sub(r"，?柔化光影(?:和留白|与留白层次|与次表面散射)?", "", text)
        text = text.replace("，只抛光已经有的材质和光，不另起一种光", "")
        text = text.replace("只抛光已经有的材质和光，不另起一种光", "")
    if _clause_affirmed(source, _FILL_ASK):
        text = text.replace("保画风与机位", "保画风")
        text = text.replace("不改机位与镜头视角", "")
        text = text.replace("不做整体 recompose / 换景别故事", "")
        text = text.replace("不做整体 recompose", "")
        text = text.replace("换景别故事", "")
        text = re.sub(r"约束：\s*；", "约束：", text)
        text = re.sub(r"约束：\s*(?=\||$)", "", text)
    if _clause_affirmed(source, _REJECT_REF_PERSON):
        text = text.replace("保持原图性别、物种、年龄段与核心外观", "")
        text = re.sub(r"；\s*；", "；", text)
        text = re.sub(r"；\s*(?=\||$)", "", text)
    text = re.sub(r"；{2,}", "；", text)
    text = re.sub(r"，{2,}", "，", text)
    text = re.sub(r"：，", "：", text)
    text = re.sub(r"个人口味:\s*；\s*", "个人口味: ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    lines: list[str] = []
    for line in text.split("\n"):
        if re.fullmatch(r"\s*-?\s*个人口味:\s*", line):
            continue
        lines.append(line)
    return "\n".join(lines).strip()
