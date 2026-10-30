"""pmem-agent 第二段对表。只产出分配，不调用任何生图或审图技能。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .skill_registry import build_registry
from .skill_specs import SKILL_SPECS

# 注册表没有这些节。命中就停，不改走普通图。
UNRECOGNIZED_JOBS = (
    "局部修",
    "设定表",
    "分镜",
    "姿势锁",
    "同一场景换光",
    "画幅延展",
    "放大清稿",
    "序列帧",
    "平铺贴图",
    "带字主视觉",
    "字标",
    "色板点选",
    "情绪板",
    "只改手",
    "只修手",
    "延展画面",
    "扩画布",
    "故事板",
    "锁姿势",
    "逐帧",
    "无缝贴图",
    "同一场景里只换光",
    "放大后清",
    "三视图设定",
)

_NAMED = re.compile(r"/pmem-([a-z0-9-]+)")
_LENS = re.compile(
    r"(几|[2-9两三四五六七八])\s*套\s*(机位|镜头|光)"
    r"|([2-9两三四五六七八])\s*个\s*机位"
    r"|镜头包|机位包|给自己挑|机位.{0,8}我来选"
)
_PIXEL_SIZE = re.compile(r"(?<![0-9第])(64|128|256)(?![0-9])")
_PIXELS = re.compile(r"像素必须同时|两张参考的像素|像素级对齐同时")
_SHOWCASE = re.compile(
    r"整页展陈|对比页|同范围重跑|多技能|全部重跑|再跑一遍|重跑一遍|同范围"
)
# 指向旧展陈「全部/同范围重跑」且未点名单支时的默认同范围清单（与主页候选展陈对齐）
_SHOWCASE_DEFAULT_FULL = (
    "draw.ordinary",
    "ui.kit",
    "icon.a",
    "icon.c",
    "merge.ladder",
    "draw.clone",
    "draw.variant",
    "style.lock",
    "prompt.write",
)
_NEG = ("不要", "别做", "不是", "不做", "别写")


@dataclass
class Handoff:
    skill: str
    section: str
    heading: str
    file: str
    deliverable: str
    pad: list[str]
    skip_pad: list[str]
    locks: str
    done: str
    next_output: str
    note: str = ""

    def complete(self) -> bool:
        return all(
            [
                self.skill,
                self.section,
                self.heading,
                self.file,
                self.deliverable,
                self.locks,
                self.done,
                self.next_output,
            ]
        )


@dataclass
class Plan:
    mode: str
    would_execute: bool
    execute: bool
    reason: str
    announce: str
    steps: list[Handoff] = field(default_factory=list)
    serial: bool = False
    parallel: bool = False
    route_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "would_execute": self.would_execute,
            "execute": self.execute,
            "reason": self.reason,
            "announce": self.announce,
            "serial": self.serial,
            "parallel": self.parallel,
            "route_ids": list(self.route_ids),
            "steps": [step.__dict__ for step in self.steps],
        }


def execute_assigned_skill(_plan: Plan) -> None:
    """路由测试的硬边界。调用即失败。"""
    raise RuntimeError("路由测试不执行技能")


def _norm_heading(text: str) -> str:
    return text.replace("`", "").strip()


def _heading_ok(heading: str, body: str) -> bool:
    want = _norm_heading(heading)
    if not want:
        return False
    for line in body.splitlines():
        got = _norm_heading(line)
        if got == want or want in got:
            return True
    return False


def _hit(text: str, word: str) -> bool:
    start = 0
    while True:
        idx = text.find(word, start)
        if idx < 0:
            return False
        prefix = text[max(0, idx - 12) : idx]
        if any(prefix.endswith(flag) or flag in prefix for flag in _NEG):
            start = idx + len(word)
            continue
        return True


def _any(text: str, words: tuple[str, ...]) -> bool:
    return any(_hit(text, word) for word in words)


def _registry() -> dict[str, Any]:
    return build_registry(SKILL_SPECS)


def _by_id(reg: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {route["id"]: route for route in reg["routes"]}


def _bodies() -> dict[str, str]:
    return {spec["name"]: spec["body"] for spec in SKILL_SPECS}


def _stop(reason: str, announce: str = "") -> Plan:
    return Plan(
        mode="stop",
        would_execute=False,
        execute=False,
        reason=reason,
        announce=announce or "没有识别到可用技能",
        serial=False,
        parallel=False,
    )


def _named_skill(text: str) -> str:
    found = _NAMED.findall(text)
    for name in found:
        if name == "agent":
            continue
        return f"pmem-{name}"
    return ""


def _icon_modes(text: str) -> set[str]:
    modes: set[str] = set()
    desktop = _any(text, ("桌面图标", "启动图标", "应用图标", "app icon", "App Icon"))
    if desktop or (_hit(text, "1024") and _any(text, ("图标", "icon", "桌面", "启动"))):
        modes.add("icon.a")
    # B 必须带线性/svg；单说「图标集」不算 B，走未分档问句
    if _any(text, ("线性", "svg", "SVG")) and _any(text, ("图标", "icon", "一套", "图标集")):
        modes.add("icon.b")
    # 「药水」单独出现常是合成梯题材，须连带图标/背包/道具格才认 C
    prop = _any(text, ("道具格", "背包", "道具图标", "装备图标")) or (
        _hit(text, "药水") and _any(text, ("图标", "背包", "道具格", "透明"))
    )
    sized = bool(_PIXEL_SIZE.search(text)) and _any(text, ("图标", "道具", "背包", "透明"))
    if prop or sized:
        modes.add("icon.c")
    return modes


def _wants_ui(text: str) -> bool:
    if _any(text, ("单张弹框", "一张弹框", "一个弹窗", "只要这一张弹窗", "就一张空弹框", "一张按钮")):
        return False
    return _any(
        text,
        (
            "整屏",
            "一整屏",
            "HUD",
            "九宫格",
            "弹窗套件",
            "弹窗套",
            "界面套件",
            "主菜单",
            "主界面",
            "按钮状态",
            "状态族",
            "一整套界面",
            "整套界面",
            "常态和按下",
            "UI套",
            "hud整屏",
        ),
    )


def _wants_merge(text: str) -> bool:
    return _any(
        text,
        (
            "合成梯",
            "一档比一档",
            "升级链",
            "八档",
            "八个等级",
            "越来越大",
            "越升越大",
            "合成升级",
            "升档",
            "L1",
            "l1",
        ),
    )


def _wants_lens(text: str) -> bool:
    if _any(text, ("镜头感", "一个镜头", "这套镜头", "选定机位", "点选后")):
        return False
    if _LENS.search(text):
        return True
    return _any(text, ("远中近", "机位包", "几套镜头", "镜头包", "几套机位"))


# 句末「变成微笑/改成姿势」= 变体；允许「再画/的她」；「变成微笑的猫」仍算换题材
_EXPR_AFTER_SWAP = re.compile(
    r"(变成|改成|换成)(一个|一下|个|张)?(微笑|生气|闭眼|侧目|眨眼|惊讶|叹气|表情|差分|姿势|动作)"
    r"(一下|差分)?(再画(一张)?|的她|的他)?$"
)


# 「不换题材 / 也不换题材」里也有「换题材」子串，禁止当成换题材
_KEEP_SUBJECT = (
    "不要换",
    "还是她",
    "还是他",
    "还是这个",
    "还是画这个",
    "不要换题材",
    "不换题材",
    "也不换题材",
    "别换题材",
    "题材不变",
    "别换人",
    "人不要换",
)
_SWAP_SUBJECT = (
    "换成",
    "改成",
    "变成",
    "新题材",
    "新角色",
    "新物件",
    "别画原来",
    "不要这个人",
    "换一个",
    "换个东西",
    "换个主题",
    "主体改成",
    "主体换成",
    "换成一只",
    "改成一只",
    "变成一只",
)
# 裸「换题材」须左边界不是「不」（覆盖 不换 / 也不换）
_SWAP_TOPIC = re.compile(r"(?<![不])换题材")


def _new_subject(text: str) -> bool:
    if _any(text, _KEEP_SUBJECT):
        return False
    # 「变成微笑 / 改成闭眼」紧贴表情 → 变体；后面还有新主体名词则仍算换题材
    if _EXPR_AFTER_SWAP.search(text) and not _any(
        text,
        (
            "新题材",
            "新角色",
            "新物件",
            "别画原来",
            "换个东西",
            "换个主题",
            "主体改成",
            "主体换成",
            "换成一只",
            "改成一只",
            "变成一只",
        ),
    ):
        return False
    if _SWAP_TOPIC.search(text):
        return True
    return _any(text, _SWAP_SUBJECT)


def _has_ref(text: str, images: list[str]) -> bool:
    return bool(images) or _any(
        text,
        (
            "参考",
            "照着",
            "照这张",
            "附图",
            "垫这张",
            "垫图",
            "垫参考",
            "这张的画风",
            "按这张",
            "抄这张",
            "跟这张",
            "仿这张",
            "这张味道",
            "这张手感",
            "这张气质",
        ),
    )


def _wants_variant(text: str) -> bool:
    if _any(text, ("画这个角色", "来一张她的立绘", "来一张他的立绘")) and not _any(
        text, ("表情", "差分", "换画风", "动作", "生气", "微笑", "变体", "表情包")
    ):
        return False
    return _any(
        text,
        (
            "换画风",
            "换个画风",
            "换个风格",
            "换个姿势",
            "换个动作",
            "换姿势",
            "换动作",
            "表情",
            "差分",
            "动作差分",
            "表情表",
            "表情包",
            "变体",
            "生气",
            "微笑",
            "闭眼",
            "侧目",
            "眨眼",
            "惊讶",
            "叹气",
            "姿势",
            "动作",
            "同一张脸",
            "同一身份",
        ),
    )


def _wants_multi(text: str, images: list[str], roles: list[str]) -> bool:
    role_set = {role for role in roles if role}
    if len(images) >= 2 and role_set >= {"identity", "structure"}:
        return True
    if _any(text, ("各管一件事", "身份图", "结构图", "这张是脸", "第一张是脸", "一张管")):
        return True
    if _any(text, ("关上", "打开", "关开")) and _any(
        text, ("另一张", "不在同一张", "身份在", "两态", "同一机位", "锁同一机位")
    ):
        return True
    return False


def _wants_key(text: str) -> bool:
    if _hit(text, "带字主视觉"):
        return False
    return _any(text, ("主视觉", "Key Art", "key art", "气氛图", "概念海报", "概念图", "宣传图", "KeyArt"))


def _wants_style(text: str) -> bool:
    return _any(
        text,
        (
            "以后按这张",
            "以后都按",
            "以后都用",
            "往后出图",
            "都用这张",
            "锁定画风",
            "锁定风格",
            "锁成风格",
            "锁风格",
            "风格锁定",
            "色板锁上",
            "以后照这个画",
        ),
    )


def _wants_critique(text: str) -> bool:
    return _any(
        text,
        (
            "只审",
            "别画",
            "不画",
            "别动笔",
            "哪里不行",
            "挑刺",
            "审图",
            "审一下",
            "审完再改",
            "审完再画",
            "先看看哪不行",
            "只评不画",
        ),
    )


def _critique_then_draw(text: str) -> bool:
    return _any(text, ("审完再改", "审完再画", "挑刺之后改"))


def _wants_atlas(text: str) -> bool:
    return _any(text, ("散图归位", "归档", "归位", "刷新图谱", "没归类", "收进图谱", "整理散图"))


def _wants_coach(text: str) -> bool:
    if not _any(text, ("进步", "短板", "知识卡")):
        return False
    return _any(text, ("看", "瞧", "给我", "想看", "怎么样", "在哪"))


def _wants_prompt(text: str) -> bool:
    if _any(text, ("提示词", "brief", "Brief", "prompt", "Prompt")) and _any(
        text,
        (
            "先不出图",
            "先别出图",
            "先别画",
            "只写提示词",
            "写提示词",
            "扩写",
            "扩成",
            "先出",
            "先写",
        ),
    ):
        return True
    return _any(text, ("扩成", "扩写")) and _any(text, ("先不出图", "先别出图", "先别画"))


def _prompt_then_draw(text: str) -> bool:
    return _wants_prompt(text) and _any(text, ("再画", "然后生图", "然后再画"))


def _unrecognized(text: str) -> str:
    for word in UNRECOGNIZED_JOBS:
        if _hit(text, word):
            return word
    return ""


def _hard(text: str) -> bool:
    return _any(text, ("到底是", "还不确定是", "界面还是单张", "UI还是插画", "图标还是插画"))


def _icon_deliverable(text: str) -> bool:
    return _any(text, ("画个图标", "画一个图标", "做图标", "一张图标", "图标母版", "要个图标"))


def _two_states(text: str) -> bool:
    return _any(text, ("关上", "关闭")) and _hit(text, "打开")


def _showcase_ids(text: str) -> list[str]:
    found: list[tuple[int, str]] = []
    probes = (
        ("界面", "ui.kit"),
        ("HUD", "ui.kit"),
        ("桌面图标", "icon.a"),
        ("1024", "icon.a"),
        ("线性", "icon.b"),
        ("svg", "icon.b"),
        ("道具", "icon.c"),
        ("合成梯", "merge.ladder"),
        ("原画", "draw.key"),
        ("普通图", "draw.ordinary"),
        ("克隆", "draw.clone"),
        ("变体", "draw.variant"),
        ("锁风格", "style.lock"),
        ("提示词", "prompt.write"),
    )
    for word, rid in probes:
        idx = text.find(word)
        if idx >= 0:
            found.append((idx, rid))
    found.sort()
    out: list[str] = []
    for _idx, rid in found:
        if rid not in out:
            out.append(rid)
    # 「全部重跑 / 同范围」未点名单支 → 默认同范围全清单，避免 showcase_unspecified
    if not out and re.search(r"全部重跑|再跑一遍|重跑一遍|同范围", text or ""):
        return list(_SHOWCASE_DEFAULT_FULL)
    return out


def _section_label(route: dict[str, Any]) -> str:
    section = str(route.get("section") or "")
    if section.startswith("Mode "):
        return section
    if route["id"].startswith("draw."):
        return section
    return section or route["id"]


def _handoff(
    route: dict[str, Any],
    *,
    deliverable: str,
    images: list[str],
    locks: str,
    done: str,
    next_output: str,
    skip: list[str] | None = None,
    note: str = "",
) -> Handoff:
    return Handoff(
        skill=route["skill"],
        section=_section_label(route),
        heading=route["heading"],
        file=route["file"],
        deliverable=deliverable,
        pad=list(images),
        skip_pad=list(skip or []),
        locks=locks,
        done=done,
        next_output=next_output,
        note=note,
    )


def _draw_done(route_id: str) -> str:
    if route_id == "draw.lens":
        return "点选前不生图，机位句子写完即停"
    if route_id == "draw.multi":
        return "这一态六维调和平均 ≥ 9.50，且身份和结构各在该在的地方"
    return "六维调和平均 ≥ 9.50，最多 4 轮"


def plan_route(
    text: str,
    *,
    images: list[str] | None = None,
    image_roles: list[str] | None = None,
    registry: dict[str, Any] | None = None,
) -> Plan:
    """对一句话做分配。execute 恒为 False。"""
    from .route_normalize import normalize_for_route

    spoken = (text or "").strip()
    # 表面折叠：搞个/味道/合成升级 → 规则词；交付物文案仍用玩家原话
    raw = normalize_for_route(spoken) if spoken else spoken
    pics = [p for p in (images or []) if p]
    roles = list(image_roles or [])
    reg = registry or _registry()
    routes = _by_id(reg)
    bodies = _bodies()

    if _PIXELS.search(raw) or _any(raw, ("像素必须同时出现",)):
        return _stop("simultaneous_pixels", "两张参考的像素要同时出现，注册表里没有这种行，停")

    banned = _unrecognized(raw)
    if banned:
        return _stop("unrecognized", f"没有识别到可用技能：{banned}")

    if _hard(raw):
        return _stop("hard_ambiguity", "还有一处硬不确定，先问这一处")

    named = _named_skill(raw)
    if named and named not in bodies and named != "pmem-draw":
        return _stop("unrecognized", "没有识别到可用技能")

    chosen: list[str] = []
    reason = ""
    draw_only = named == "pmem-draw"
    showcase_ids = _showcase_ids(raw) if _SHOWCASE.search(raw) else []

    if named in {"pmem-ui", "pmem-merge-ladder", "pmem-style-lock", "pmem-critique", "pmem-atlas", "pmem-coach", "pmem-prompt"}:
        chosen = {
            "pmem-ui": ["ui.kit"],
            "pmem-merge-ladder": ["merge.ladder"],
            "pmem-style-lock": ["style.lock"],
            "pmem-critique": ["critique.review"],
            "pmem-atlas": ["atlas.file"],
            "pmem-coach": ["coach.report"],
            "pmem-prompt": ["prompt.write"],
        }[named]
        reason = "named"
    elif not draw_only and len(showcase_ids) >= 2:
        chosen = showcase_ids
        reason = "showcase"
    elif not draw_only and (named == "pmem-icon" or (not named and _icon_deliverable(raw)) or _icon_modes(raw)):
        modes = _icon_modes(raw)
        if len(modes) > 1:
            return _stop("icon_conflict", "图标 A/B/C 同时命中，只问这一处")
        if len(modes) == 1:
            chosen = [next(iter(modes))]
            reason = "icon"
        elif named == "pmem-icon" or _icon_deliverable(raw):
            return _stop("icon_unspecified", "只说图标，A/B/C 没分开，先问这一处")
    elif not draw_only and len(showcase_ids) == 1:
        chosen = showcase_ids
        reason = "showcase"
    elif not draw_only and _SHOWCASE.search(raw):
        return _stop("showcase_unspecified", "展陈没写要重跑哪几支")

    if not chosen:
        if not draw_only and _wants_ui(raw):
            chosen = ["ui.kit"]
            reason = "ui"
        elif not draw_only and _wants_merge(raw):
            chosen = ["merge.ladder"]
            reason = "merge"
        elif _wants_lens(raw):
            chosen = ["draw.lens"]
            reason = "lens"
        elif _wants_multi(raw, pics, roles):
            chosen = ["draw.multi"]
            reason = "multi"
        elif _wants_variant(raw) and _any(raw, ("同一张脸", "同一身份", "还是她", "还是他", "别换人")):
            # 已锁同一身份时，表情/姿势优先变体，避免被「改成」误抢成克隆
            chosen = ["draw.variant"]
            reason = "variant"
        elif "走普通图" in raw and not _new_subject(raw):
            # 点名普通图优先于近邻/子串误伤；真换题材仍走克隆
            chosen = ["draw.ordinary"]
            reason = "named_ordinary"
        elif _has_ref(raw, pics) and _new_subject(raw):
            chosen = ["draw.clone"]
            reason = "clone"
        elif _wants_variant(raw):
            chosen = ["draw.variant"]
            reason = "variant"
        elif _wants_key(raw):
            chosen = ["draw.key"]
            reason = "key"
        elif not draw_only and _prompt_then_draw(raw):
            chosen = ["prompt.write", "draw.ordinary"]
            reason = "prompt_then_draw"
        elif not draw_only and _critique_then_draw(raw):
            chosen = ["critique.review", "draw.ordinary"]
            reason = "critique_then_draw"
        elif not draw_only and _wants_style(raw):
            chosen = ["style.lock"]
            reason = "style"
        elif not draw_only and _wants_prompt(raw) and _wants_critique(raw) and _any(
            raw, ("只审", "挑刺", "审图", "只评")
        ):
            return _stop("hard_ambiguity", "提示词和只审同时出现，先问这一处")
        elif not draw_only and _wants_prompt(raw):
            # 提示词意图优先于「别画」审图，避免「先写提示词别画」误进 critique
            chosen = ["prompt.write"]
            reason = "prompt"
        elif not draw_only and _wants_critique(raw):
            chosen = ["critique.review"]
            reason = "critique"
        elif not draw_only and _wants_atlas(raw):
            chosen = ["atlas.file"]
            reason = "atlas"
        elif not draw_only and _wants_coach(raw):
            chosen = ["coach.report"]
            reason = "coach"
        else:
            chosen = ["draw.ordinary"]
            reason = "default"

    steps: list[Handoff] = []
    route_ids: list[str] = []
    for rid in chosen:
        route = routes.get(rid)
        if not route or not route.get("routable"):
            return _stop("unrecognized", "没有识别到可用技能")
        if not _heading_ok(route["heading"], bodies.get(route["skill"], "")):
            return _stop("stale_registry", "注册表过期，先跑 python3 pmem_art.py skills --install")
        if rid == "draw.multi" and _two_states(raw):
            route_ids.append(rid)
            steps.append(
                _handoff(
                    route,
                    deliverable="先交关上这一态",
                    images=pics,
                    locks="身份图的身份；机位以结构图为准，身份图原来的机位作废",
                    done=_draw_done(rid),
                    next_output="通过的关上这一张",
                    note="converge start --contract split，不要写 --scale medium",
                )
            )
            route_ids.append(rid)
            steps.append(
                _handoff(
                    route,
                    deliverable="只改成打开这一态",
                    images=["上一步通过的那张"],
                    locks="机位不变，只改开合",
                    done=_draw_done(rid),
                    next_output="打开这一张",
                    skip=pics,
                    note="只垫已经通过的那张",
                )
            )
            continue
        locks = "按这一节的合同"
        done = "这一节自己的完成线"
        note = ""
        if rid.startswith("draw."):
            locks = "身份、画风和机位按这一节；普通图锁机位"
            done = _draw_done(rid)
            if rid == "draw.ordinary":
                note = "单张、medium、最多 4 轮、合格线 9.50。不说成多图分工"
                locks = "锁机位和身份。多张参考留在列表里，生成只垫宽高比对齐的那张"
        elif rid == "ui.kit":
            done = "概念、组件、九宫格、状态族都过 9.50"
            locks = "整套界面，不用单张插画交差"
        elif rid.startswith("icon."):
            done = "该档母版或图标过 9.50，A/B/C 不混"
            locks = route["when"]
        elif rid == "merge.ladder":
            done = "八件关系说得通之后，每档正方形 ≥ 9.50"
            locks = "同一条升级链，不改成另一套东西"
        elif rid == "prompt.write":
            done = "交出提示词方案，不生图"
            locks = "只写提示词"
        elif rid == "critique.review":
            done = "六维审完，不生图"
            locks = "只审"
        elif rid == "style.lock":
            done = "色板和禁用词锁上，不生图"
            locks = "以后按这张"
        elif rid == "atlas.file":
            done = "散图归位，不生图"
            locks = "只归档"
        elif rid == "coach.report":
            done = "进步、短板或知识卡交卷，知识卡不自动写入"
            locks = "只读报告"
        route_ids.append(rid)
        steps.append(
            _handoff(
                route,
                deliverable=spoken[:80] or route["when"],
                images=pics,
                locks=locks,
                done=done,
                next_output="这一步的成图或文字结论",
                note=note,
            )
        )

    mode = "default" if chosen == ["draw.ordinary"] else "skill"
    labels = "、".join(_section_label(routes[rid]) for rid in chosen)
    return Plan(
        mode=mode,
        would_execute=True,
        execute=False,
        reason=reason,
        announce=f"按 {labels} 走了",
        steps=steps,
        serial=len(steps) > 1,
        parallel=False,
        route_ids=route_ids,
    )
