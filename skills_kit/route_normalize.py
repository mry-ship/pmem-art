"""美术口语 → 标准路由句（本地启发式 + 供 Agent 填写的模板词）。

检索仍是字面/ n-gram 相似；口语靠「先标准化」抬召回，不做向量语义。
规则分流以 plan_route 为准；认路前可做短口语表面折叠（rewrite_colloquial）。
标准句用于检索增强与双路交叉校验。
深度表见 skills_kit/data/colloquial_expand.jsonl（≥8000）。
"""
from __future__ import annotations

import re
from typing import Any

from .colloquial_lexicon import expand_terms, load_lexicon, rewrite_colloquial

# 兼容旧引用：懒加载深度表
COLLOQUIAL_EXPAND: dict[str, list[str]] = load_lexicon()

# Agent 写标准句时应用的固定模板（短、可机读）
CANON_TEMPLATES: dict[str, str] = {
    # 禁止写「不换题材」：子串「换题材」曾把标准句二次规则误判成克隆
    "draw.ordinary": "要画一张图；有参考；题材不变；走普通图",
    "draw.clone": "有参考图；换新题材；锁画风；走克隆",
    "draw.variant": "同一身份；换表情或动作或画风；机位已在图上；走变体",
    "draw.multi": "多张附图各管一件事；或关开态要锁同一机位；走多图分工",
    "draw.lens": "要几套机位或镜头包给玩家挑；先不出成图；走镜头包",
    "draw.key": "主视觉或概念海报；走原画",
    "ui.kit": "整套界面或 HUD 或九宫格与状态族；走界面",
    "icon.a": "1024 桌面启动图标母版；走图标A",
    "icon.b": "一套线性 SVG 图标；走图标B",
    "icon.c": "背包道具透明底栅格图标；走图标C",
    "merge.ladder": "同一套东西一档比一档大；走合成梯",
    "style.lock": "以后按这张色板画风；走锁风格；不生图",
    "critique.review": "只审不画；走审图",
    "atlas.file": "散图归位；走归档",
    "coach.report": "看进步或短板或知识卡；走教练",
    "prompt.write": "先写提示词；先不出图；走提示词",
    "stop.hard": "交付类型互斥；硬不确定；先问玩家",
    "stop.unrecognized": "注册表没有这种节；停；不改走普通图",
}


def expand_colloquial(text: str) -> str:
    """把口语碎片展开成带标准词的增广句（只用于检索，不改原话）。"""
    return expand_terms(text, COLLOQUIAL_EXPAND)


def normalize_for_route(text: str) -> str:
    """认路用表面折叠：只做短口语替换，不追加检索 extras（防污染规则）。"""
    return rewrite_colloquial(text, COLLOQUIAL_EXPAND, append_extras=False)


def _has(text: str, *pats: str) -> bool:
    return any(re.search(p, text) for p in pats)


def _negated(text: str, word: str) -> bool:
    # 「别画原来」不是在否定「换成」；认「不换/也不换/别换/不要换…」
    if word == "换":
        if re.search(r"(不|也不|不要|别|不是|不做)\s*换(题材|人|东西|主体)?|题材不变", text):
            # 句里若另有真正的「换成/主体改成」，仍不算整句否定
            if re.search(r"(?<![不])换成|(?<![不])换题材|主体改成|主体换成", text):
                return False
            return True
        return False
    return bool(re.search(rf"(不要|别|不是|不做).{{0,4}}{re.escape(word)}", text))


def infer_signals(
    text: str,
    *,
    images: list[str] | None = None,
    image_roles: list[str] | None = None,
) -> dict[str, Any]:
    raw = text or ""
    pics = [p for p in (images or []) if p]
    roles = [r for r in (image_roles or []) if r]
    return {
        "has_ref": bool(pics) or _has(raw, r"参考|照这张|照着|垫这张|按这张"),
        # 「换题材」须左不是「不」，避免「不换题材/也不换题材」误判
        "new_subject": (
            _has(raw, r"换成|(?<![不])换题材|别画原来|主体改成|换个东西|改成一只|改成一")
            and not _negated(raw, "换")
        ),
        "keep_subject": _has(
            raw, r"不要换题材|不换题材|也不换题材|题材不变|还是画这个|别换人|别换题材"
        ),
        "variant": _has(raw, r"表情|差分|换个画风|同一张脸|同一身份"),
        "multi": _has(raw, r"各管一件事|第一张是脸|身份在第一张")
        or ({"identity", "structure"} <= set(roles)),
        "two_state": _has(raw, r"关上|打开|关开"),
        "lens": _has(raw, r"几套机位|镜头包|机位包|给自己挑|几套镜头")
        and not _has(raw, r"只要一张|镜头感"),
        "ui": _has(raw, r"整套界面|一整屏|HUD|九宫格|主菜单|状态族"),
        "icon_a": _has(raw, r"1024|桌面图标|启动图标|应用图标"),
        "icon_b": _has(raw, r"线性\s*svg|线性图标|svg\s*图标"),
        "icon_c": _has(raw, r"背包|道具格|透明底") and _has(raw, r"64|128|256|图标"),
        "merge": _has(raw, r"合成梯|一档比一档|越升越大|合成升级"),
        "key": _has(raw, r"主视觉|概念海报|Key\s*Art|气氛图"),
        "style": _has(raw, r"以后按这张|锁风格|都用这张的色"),
        # 「别画原来的人」是克隆信号，不要误判成只审
        "critique": (
            _has(raw, r"只审|先看看哪不行")
            or (_has(raw, r"别画") and not _has(raw, r"别画原来|别画出"))
        )
        and not _has(raw, r"审完再改"),
        "atlas": _has(raw, r"散图归位|收进图谱"),
        "coach": _has(raw, r"进步|短板|知识卡"),
        "prompt_only": _has(raw, r"先写提示词|先不出图|先别画"),
        "hard": _has(raw, r"到底是整套|还是一张插画|还是单张"),
        "image_count": len(pics),
        "roles": roles,
    }


def build_canonical_brief(
    text: str,
    *,
    images: list[str] | None = None,
    image_roles: list[str] | None = None,
) -> dict[str, Any]:
    """本地启发式标准路由句。Agent 应用自己的标准句覆盖；冲突时 advise 会降置信。"""
    sig = infer_signals(text, images=images, image_roles=image_roles)
    rid = "draw.ordinary"
    if sig["hard"]:
        rid = "stop.hard"
    elif sig["icon_a"] and sig["icon_b"]:
        rid = "stop.hard"
    elif sig["ui"]:
        rid = "ui.kit"
    elif sig["icon_a"]:
        rid = "icon.a"
    elif sig["icon_b"]:
        rid = "icon.b"
    elif sig["icon_c"]:
        rid = "icon.c"
    elif sig["merge"]:
        rid = "merge.ladder"
    elif sig["lens"]:
        rid = "draw.lens"
    elif sig["multi"] or sig["two_state"]:
        rid = "draw.multi"
    elif sig["has_ref"] and sig["new_subject"] and not sig["keep_subject"]:
        rid = "draw.clone"
    elif sig["variant"]:
        rid = "draw.variant"
    elif sig["key"]:
        rid = "draw.key"
    elif sig["style"]:
        rid = "style.lock"
    elif sig["critique"]:
        rid = "critique.review"
    elif sig["atlas"]:
        rid = "atlas.file"
    elif sig["coach"]:
        rid = "coach.report"
    elif sig["prompt_only"]:
        rid = "prompt.write"
    elif sig["has_ref"] and sig["keep_subject"]:
        rid = "draw.ordinary"

    template = CANON_TEMPLATES.get(rid, CANON_TEMPLATES["draw.ordinary"])
    # 附一点原话锚点，方便人看，不干扰关键词
    tip = (text or "").strip().replace("\n", " ")[:40]
    canonical = template if not tip else f"{template}。原话要点：{tip}"
    return {
        "canonical": canonical,
        "guess_route_id": rid,
        "template": template,
        "signals": sig,
        "source": "local_heuristic",
    }
