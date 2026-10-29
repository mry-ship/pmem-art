"""Subject lexicon and bilingual structure sentences.

分类词中英都参与匹配（用户 brief 两种语言都会写）。
结构句、回流句各有中英两套：中文回显给你看，写入生图提示词时用英文。
词条不设上限；中文用长短语，单字只带排除表。英文按整词。
"""
from __future__ import annotations

import re
from typing import Any

_LATIN_TOKEN = re.compile(r"[a-z0-9]+")

# --- 给人看的中文词（长短语）。单字不放这里。 ---
HUMANOID_ZH: tuple[str, ...] = (
    "人物", "少女", "少年", "女侠", "男侠", "孤侠", "女孩", "男孩", "女人", "男人",
    "人像", "肖像", "半身像", "全身像", "坐姿", "站姿", "骑士", "法师", "战士", "旅人",
    "小孩", "儿童", "婴儿", "幼儿", "少妇", "老者", "老人", "老头", "老太",
    "公主", "王子", "女王", "国王", "皇帝", "皇后", "武士", "剑客", "刺客", "忍者",
    "海盗", "船长", "水手", "士兵", "将军", "医生", "护士", "学生", "画家", "舞者",
    "厨师", "猎人", "渔夫", "女巫", "巫师", "牧师", "游侠", "弓手", "枪手", "机甲师",
    "飞行员", "驾驶员", "美女", "帅哥", "姑娘", "小伙", "人类", "侠客", "新娘", "新郎",
    "情侣", "路人", "行人", "模特", "铁匠", "牛仔", "兽人", "角色",
)

CREATURE_ZH: tuple[str, ...] = (
    "猫咪", "小猫", "幼猫", "小狗", "幼犬", "飞龙", "巨龙", "幼龙", "飞鸟", "战马",
    "动物", "狐狸", "白狐", "赤狐", "野狼", "老虎", "狮子", "豹子", "猎豹", "大象",
    "长颈鹿", "斑马", "熊猫", "兔子", "白兔", "松鼠", "刺猬", "蝙蝠", "猴子", "棕熊",
    "白熊", "北极熊", "梅花鹿", "麋鹿", "驯鹿", "山羊", "绵羊", "奶牛", "水牛", "野猪",
    "骏马", "小马", "公鸡", "母鸡", "鸽子", "老鹰", "雄鹰", "猫头鹰", "乌鸦", "天鹅",
    "孔雀", "企鹅", "鹦鹉", "蟒蛇", "蜥蜴", "鳄鱼", "乌龟", "海龟", "青蛙", "恐龙",
    "翼龙", "金鱼", "鲨鱼", "鲸鱼", "海豚", "章鱼", "螃蟹", "龙虾", "蝴蝶", "蜜蜂",
    "蜘蛛", "独角兽", "凤凰", "麒麟", "狮鹫", "史莱姆", "狼人", "幼兽", "萌宠",
)
MECH_ZH: tuple[str, ...] = (
    "机甲", "机器人", "机械兽", "高达", "无人机", "赛博格", "机械人", "自律机兵",
)
SCENE_ZH: tuple[str, ...] = (
    "空镜", "无人", "纯风景", "纯场景", "无人物", "峡谷", "天际", "风景", "城市",
    "城镇", "街景", "森林", "雨林", "沙漠", "戈壁", "草原", "雪山", "冰川", "海洋",
    "海滩", "湖面", "瀑布", "火山", "星空", "夜空", "云海", "废墟", "遗迹", "码头",
    "港口", "桥梁", "大厦", "塔楼",
)
# 任务型 UI：整句就是界面套件，即使提到一只猫也跳过结构句。
TASK_UI_ZH: tuple[str, ...] = (
    "九宫格", "图标集", "矢量图标", "界面套件", "主界面套件",
)
# 只是提到，不能单独把整句判成 UI。
MENTION_UI_ZH: tuple[str, ...] = (
    "界面", "按钮", "菜单", "弹窗", "主菜单", "状态栏", "血条", "技能栏", "小地图",
)

# 单字 + 排除。排除词出现时，这个单字不算命中。
HUMANOID_SINGLES: tuple[tuple[str, tuple[str, ...]], ...] = ()
CREATURE_SINGLES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("龙", ("龙虾", "龙门", "龙骨", "龙井", "龙套", "龙舌兰")),
    ("猫", ("猫头鹰",)),
    ("狗", ("热狗", "狗尾草")),
    ("鹿", ("逐鹿", "鹿角", "鹿茸")),
    ("狼", ("狼藉", "狼狈")),
    ("虎", ("虎口", "马虎", "虎符")),
    ("熊", ("熊市", "熊猫")),  # 熊猫已是短语
    ("鹰", ()),
    ("蛇", ("蛇年",)),
    ("鱼", ("鱼贯", "鱼目")),
    ("马", ("马上", "码头", "马赛克", "马力", "马拉松", "马虎")),
    ("牛", ("牛奶", "牛排", "牛市")),
    ("羊", ("羊绒", "羊毛")),
    ("鸟", ("鸟枪", "鸟瞰")),
)

HUMANOID_EN = frozenset({
    "girl", "boy", "woman", "man", "portrait", "character", "knight", "warrior",
    "mage", "wizard", "person", "people", "hero", "heroine", "human", "lady",
    "gentleman", "queen", "king", "prince", "princess", "witch", "sorcerer",
    "soldier", "pirate", "ninja", "samurai", "monk", "priest", "child", "kid",
    "baby", "toddler", "teen", "elder", "archer", "rogue", "paladin", "necromancer",
    "druid", "shaman", "bard", "dancer", "singer", "chef", "doctor", "nurse",
    "teacher", "student", "hunter", "fisher", "farmer", "blacksmith", "pilot",
    "captain", "sailor", "cowboy", "orc", "goblin",
})
CREATURE_EN = frozenset({
    "dragon", "drake", "wyvern", "cat", "kitten", "dog", "puppy", "wolf", "fox",
    "bird", "horse", "creature", "animal", "deer", "stag", "doe", "bear", "lion",
    "tiger", "elephant", "rabbit", "mouse", "rat", "snake", "fish", "shark",
    "whale", "dolphin", "owl", "eagle", "hawk", "phoenix", "unicorn", "griffin",
    "slime", "dinosaur", "dino", "spider", "butterfly", "bee", "cow", "sheep",
    "pig", "goat", "chicken", "duck", "goose", "frog", "turtle", "crocodile",
    "lizard", "puppy", "kitten", "werewolf", "pet",
})
MECH_EN = frozenset({
    "mecha", "mech", "robot", "android", "cyborg", "automaton", "gundam",
})
# 航拍平台。和场景词同时出现时不当成机甲。
_CAMERA_PLATFORM_ZH = frozenset({"无人机"})
SCENE_EN = frozenset({
    "landscape", "cityscape", "canyon", "skyline", "architecture", "scenery",
    "forest", "desert", "ocean", "beach", "mountain", "ruins", "vista", "seascape",
})
TASK_UI_EN = frozenset({"hud"})
TASK_UI_PHRASES = ("ui kit", "app icon", "icon set")
# 「ui / button / menu」只是提到。单独成句才算界面；和人物或场景同句时跟主体。
MENTION_UI_EN = frozenset({"button", "menu", "ui"})
# 整词碰撞：bee line / king bed / pet project 不是主体。先从句子里抹掉再切词。
_FALSE_FRIEND_PHRASES = (
    re.compile(r"\bbeeline\b"),
    re.compile(r"\bbee\s+line\b"),
    re.compile(r"\bking\s+bed\b"),
    re.compile(r"\bqueen\s+bed\b"),
    re.compile(r"\bking[\s-]size\b"),
    re.compile(r"\bqueen[\s-]size\b"),
    re.compile(r"\bpet\s+project\b"),
)
# 必须贴着词本身。窗口里随便出现「非」会误伤「非常卡通」。
_TOY_NEGATION = (
    "不要", "禁止", "不用", "避免", "不是", "并非", "勿", "别", "非",
    "don't ", "dont ", "not ", "no ",
)

# 中文给你看，英文写入提示词。
FLOORS: dict[str, dict[str, str]] = {
    "humanoid": {
        "zh": (
            "结构底线：双肩双肘双腕关节自然连续，握持受力真实，双眼瞳孔同向同高；"
            "接触阴影与承托可读；禁止肢体融化进道具"
        ),
        "en": (
            "Structure floor: shoulder, elbow, and wrist joints stay continuous, grips take real weight, "
            "both pupils share direction and height; contact shadows read; do not melt limbs into props"
        ),
    },
    "creature": {
        "zh": (
            "结构底线：肢体数量与关节符合该物种，四足、翼或尾的连接清楚；"
            "接触阴影与承托可读；禁止多肢融化。不要改成人类双肘或强制双眼"
        ),
        "en": (
            "Structure floor: limb count and joints match this species, and legs, wings, or the tail connect clearly; "
            "contact shadows read; do not melt extra limbs. Do not convert this into a human elbow pair or force two eyes"
        ),
    },
    "both": {
        "zh": (
            "结构底线：人物关节与握持清楚，双眼瞳孔同向；动物按物种连接肢体，不要改成人类双肘；"
            "接触阴影可读；禁止肢体融化进道具"
        ),
        "en": (
            "Structure floor: the person's joints and grip stay clear and both pupils share a direction; "
            "the animal's limbs follow its species and are not converted into human elbows; "
            "contact shadows read; do not melt limbs into props"
        ),
    },
    "mechanical": {
        "zh": (
            "结构底线：机械关节、装甲接缝与管线连接清楚，承重点有接触阴影；"
            "禁止部件融化。不要改成人类双眼或软组织肘"
        ),
        "en": (
            "Structure floor: mechanical joints, armor seams, and cable links stay readable, "
            "with contact shadows under load points; do not melt parts. "
            "Do not turn this into human eyes or soft elbows"
        ),
    },
    "generic": {
        "zh": "结构底线：主体轮廓连续，承托与接触阴影可读；禁止结构融化",
        "en": (
            "Structure floor: the subject silhouette stays continuous, supports and contact shadows read; "
            "do not melt the structure"
        ),
    },
    "scene": {
        "zh": "结构底线：空间透视灭点收束与体块接触阴影清楚；禁止结构融化",
        "en": (
            "Structure floor: vanishing points converge and mass contact shadows read; "
            "do not melt the structure"
        ),
    },
    "ui_shell": {
        "zh": (
            "结构底线：可九宫格弹框母版——内容区必须大块留白/纯色可双向拉伸，"
            "禁止礼盒道具插画进内容区；仅角花与顶栏小徽章(motif≤1)；底栏符号钮禁可读字"
        ),
        "en": (
            "Structure floor: 9-slice popup shell — large empty stretchable plain content zone, "
            "NO gift box or prop illustration inside the content area; corner chrome only plus "
            "at most one top badge motif; bottom symbol buttons only, NO readable text"
        ),
    },
    "clone_subject": {
        "zh": (
            "结构底线：Mode B 垫参考只锁 medium/材质/描边——新题材主体 silhouette 必须独占画面，"
            "禁止复制参考 prop（如礼盒）外形；brief 写清新主体名词"
        ),
        "en": (
            "Structure floor: Mode B style ref locks medium/chrome only — the NEW subject silhouette "
            "must dominate the frame; do NOT photocopy the reference prop shape (e.g. gift box); "
            "name the new subject explicitly in the brief"
        ),
    },
}

_UI_SHELL_GOAL_MARKERS: tuple[str, ...] = (
    "空内容",
    "空中心",
    "留白",
    "可拉伸",
    "九宫格母版",
    "弹框母版",
    "弹窗母版",
    "popup shell",
    "empty content",
    "9-slice mother",
    "stretchable center",
    "content area empty",
    "禁止礼盒",
    "禁礼盒",
    "禁止礼物",
    "no props in center",
    "no gift box in center",
)

_UI_SHELL_ECHO_MARKERS: tuple[str, ...] = (
    "中心有礼盒",
    "心形礼盒",
    "抄礼盒",
    "礼盒进内容",
    "内容区有",
    "非空中心",
    "奖励插画",
    "换皮手游",
    "礼物盒画进",
    "抄参考主体",
    "回声参考",
    "gift box in center",
    "reference motif in center",
    "prop in content area",
)


_UI_SHELL_CENTER_ART_MARKERS: tuple[str, ...] = (
    "中心插画",
    "奖励插画",
    "center illustration",
    "reward illustration",
    "center motif art",
    "内容区有物",
)

_NEGATION_BEFORE_UI_CENTER_ART = re.compile(
    r"(?:非|并非|无|禁止|不要|勿|未|别|no\s|not\s)[\s\S]{0,6}$",
    re.IGNORECASE,
)


def _affirmative_ui_center_art_marker(blob: str, marker: str) -> bool:
    """True if ``marker`` appears in ``blob`` and is not negated (e.g. 非奖励插画)."""
    low = (blob or "").lower()
    m = (marker or "").lower()
    if not m or m not in low:
        return False
    start = 0
    while True:
        idx = low.find(m, start)
        if idx < 0:
            return False
        prefix = low[max(0, idx - 14) : idx]
        if not _NEGATION_BEFORE_UI_CENTER_ART.search(prefix):
            return True
        start = idx + len(m)
    return False


def ui_shell_clone_task(
    *,
    goal: str = "",
    ref_analysis: Any = "",
    module: str = "",
) -> bool:
    """True when a ui.* converge goal is an empty 9-slice popup chrome shell (Clone UI path)."""
    mod_l = (module or "").strip().lower()
    if mod_l not in ("ui",) and not mod_l.startswith("ui."):
        return False
    if isinstance(ref_analysis, dict):
        ra_str = " ".join(str(v or "") for v in ref_analysis.values())
    else:
        ra_str = str(ref_analysis or "")
    blob = f"{goal or ''} {ra_str}".lower()
    if mod_l == "ui.popupclone" or mod_l.endswith(".popupclone"):
        if any(_affirmative_ui_center_art_marker(blob, m) for m in _UI_SHELL_CENTER_ART_MARKERS):
            return False
        return True
    return any(m.lower() in blob for m in _UI_SHELL_GOAL_MARKERS)


def ui_shell_echo_marked(text: str) -> bool:
    """Defects/strengths text flags reference-subject echo inside popup content zone."""
    low = (text or "").lower()
    return any(m.lower() in low for m in _UI_SHELL_ECHO_MARKERS)


_CLONE_NEW_SUBJECT_GOAL_MARKERS: tuple[str, ...] = (
    "clone mode b",
    "mode b",
    "新题材",
    "垫",
    "只锁medium",
    "只借",
    "不抄",
    "换新",
)

_CLONE_SUBJECT_ECHO_MARKERS: tuple[str, ...] = (
    "完全抄参考",
    "抄参考主体",
    "抄参考",
    "抄礼盒",
    "复制参考",
    "未生成钥匙",
    "未换题材",
    "题材回声",
    "礼盒主体",
    "心形礼盒",
    "仍是参考",
    "主体仍是",
    "photocopy",
    "near-duplicate",
    "reference prop copied",
    "prop copied",
    "gift box as subject",
    "回声参考",
)


def clone_style_lock_new_subject_task(
    *,
    goal: str = "",
    ref_analysis: Any = "",
    module: str = "",
    ref_image: str = "",
) -> bool:
    """Mode B icon/character clone: style ref present and brief expects a NEW subject."""
    if not str(ref_image or "").strip():
        return False
    mod_l = (module or "").strip().lower()
    if not (mod_l.startswith("icon.") or mod_l.startswith("character.")):
        return False
    if isinstance(ref_analysis, dict):
        ra_str = " ".join(str(v or "") for v in ref_analysis.values())
    else:
        ra_str = str(ref_analysis or "")
    blob = f"{goal or ''} {ra_str}".lower()
    if "clone mode b" in blob or ("mode b" in blob and "clone" in blob):
        return True
    return any(m.lower() in blob for m in _CLONE_NEW_SUBJECT_GOAL_MARKERS)


def clone_subject_echo_marked(text: str) -> bool:
    """Defects flag copying reference prop instead of the briefed new subject."""
    low = (text or "").lower()
    return any(m.lower() in low for m in _CLONE_SUBJECT_ECHO_MARKERS)

# 回流模板。judge 回显用 zh，生图提示词用 en。
REFLOW: dict[str, dict[str, str]] = {
    "anatomy": {
        "zh": "解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边",
        "en": "Anatomy and perspective: fix joint links, grip, hands and feet, and contact shadows; do not melt edges",
    },
    "texture": {
        "zh": "质感：锐化轮廓与材质分界，抑制融化边缘，勿用噪点冒充细节",
        "en": "Texture: sharpen silhouettes and material boundaries; do not fake detail with noise",
    },
    "light_weak": {
        "zh": "光影：理顺主光方向与明暗交接，勿用光效掩盖结构问题",
        "en": "Lighting: settle the key-light direction and the shadow edge; do not hide structure behind effects",
    },
    "light_ok": {
        "zh": "光影：理顺主光方向与明暗交接，只抬画面里已经有的光",
        "en": "Lighting: settle the key-light direction and the shadow edge; only raise light that is already in the picture",
    },
    "composition": {
        "zh": "构图：稳住主体可读性与层次，勿新增冲突焦点",
        "en": "Composition: keep the subject readable and the depth layers stable; do not add a competing focal point",
    },
    "fallback_structure": {
        "zh": "优先修复结构与边缘完整",
        "en": "Fix structure and edge integrity first",
    },
    "fallback_texture": {
        "zh": "优先恢复边缘锐度与材质区分",
        "en": "Restore edge sharpness and material separation first",
    },
    "fallback_small": {
        "zh": "小步修正最低分维，保持原机位与身份",
        "en": "Make a small fix on the lowest dimension and keep the camera and identity",
    },
    "scene_fix": {
        "zh": "透视：收束灭点与体块接触阴影，禁止结构融化",
        "en": "Perspective: pull vanishing points together and keep mass contact shadows; do not melt the structure",
    },
    "creature_fix": {
        "zh": "解剖：按该物种接好肢体与翼或尾，禁止多肢融化，不要改成人类双肘",
        "en": "Anatomy: connect limbs, wings, or the tail for this species; do not melt extra limbs or convert them into human elbows",
    },
    "mech_fix": {
        "zh": "结构：接好机械关节、装甲接缝与管线，禁止部件融化，不要改成人类双眼",
        "en": "Structure: connect mechanical joints, armor seams, and cables; do not melt parts or turn them into human eyes",
    },
    "camera": {
        "zh": "保持新机位：{dir}",
        "en": "Keep the new camera: {dir}",
    },
    "missing_dim": {
        "zh": "补全透视与解剖评分并修正结构硬伤，禁止糊边融边",
        "en": "Score perspective and anatomy, then fix the structural break; do not melt edges",
    },
}

_TOY_STUBS: tuple[re.Pattern[str], ...] = (
    re.compile(r"chunky\s+vinyl(?:\s*-\s*|\s+)toy", re.I),
    re.compile(r"vinyl(?:\s*-\s*|\s+)toy", re.I),
    re.compile(r"\bvinyl\b", re.I),
    re.compile(r"\bchibi\b", re.I),
    re.compile(r"搪胶"),
    re.compile(r"桶身"),
    re.compile(r"金琥珀双描边"),
    re.compile(r"barrel[\s-]*torso", re.I),
    re.compile(r"dual[\s-]*rim", re.I),
)
_TOY_ALLOW = (
    "玩具", "q版", "卡通", "软塑", "盲盒", "搪胶", "chibi", "vinyl", "toy",
    "cute cartoon",
)


def latin_tokens(blob: str) -> set[str]:
    return set(_LATIN_TOKEN.findall((blob or "").lower()))


def _phrase_hits(blob: str, phrases: tuple[str, ...]) -> list[str]:
    return [p for p in phrases if p and p in blob]


def _spans(blob: str, phrase: str) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    start = 0
    while True:
        idx = blob.find(phrase, start)
        if idx < 0:
            return spans
        spans.append((idx, idx + len(phrase)))
        start = idx + len(phrase)


def _single_hit(
    blob: str,
    singles: tuple[tuple[str, tuple[str, ...]], ...],
    covered_by: tuple[str, ...] = (),
) -> bool:
    """A single character counts only outside a longer phrase or its own exclude (马 in 码头)."""
    covers = [span for phrase in covered_by for span in _spans(blob, phrase)]
    for ch, excludes in singles:
        blocked = covers + [span for ex in excludes for span in _spans(blob, ex)]
        start = 0
        while True:
            idx = blob.find(ch, start)
            if idx < 0:
                break
            if any(a <= idx < b for a, b in blocked):
                start = idx + len(ch)
                continue
            return True
    return False


def _strip_false_friends(blob: str) -> str:
    cleaned = blob
    for pat in _FALSE_FRIEND_PHRASES:
        cleaned = pat.sub(" ", cleaned)
    return cleaned


def _affirmative_hit(blob: str, token: str) -> bool:
    """Chinese phrases match by text. Latin tokens match whole words, so toy does not hit destroy."""
    if token.isascii():
        hits = list(re.finditer(rf"\b{re.escape(token)}\b", blob))
    else:
        hits = []
        start = 0
        while True:
            idx = blob.find(token, start)
            if idx < 0:
                break
            hits.append(idx)
            start = idx + len(token)
    for hit in hits:
        idx = hit if isinstance(hit, int) else hit.start()
        prefix = blob[max(0, idx - 8) : idx].rstrip()
        if any(prefix.endswith(neg) for neg in _TOY_NEGATION):
            continue
        return True
    return False


def _drop_shorter_inside_longer(hits: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Drop a cue that is only a substring of a longer cue also present."""
    ordered = sorted(hits, key=lambda item: len(item[1]), reverse=True)
    kept: list[tuple[str, str]] = []
    for kind, phrase in ordered:
        if any(phrase != other and phrase in other for _k, other in kept):
            continue
        kept.append((kind, phrase))
    return kept


def classify_subject_kind(
    *,
    goal: str = "",
    ref_analysis: Any = "",
    ref_image: str = "",
    module: str = "",
) -> str:
    """ui | humanoid | creature | both | mechanical | scene | generic | unknown."""
    mod_l = (module or "").strip().lower()
    _ = ref_image  # filename and folder stay out of the cue blob
    if isinstance(ref_analysis, dict):
        ra_str = " ".join(str(v or "") for v in ref_analysis.values())
    else:
        ra_str = str(ref_analysis or "")
    # 模块名和参考图路径不进词表。character.Pet、文件夹 ui、文件名 portrait 都不能改判正文。
    blob = _strip_false_friends(f"{goal or ''} {ra_str}".lower())
    tokens = latin_tokens(blob)

    if mod_l in ("ui", "icon") or mod_l.startswith(("ui.", "icon.")):
        return "ui"

    raw: list[tuple[str, str]] = []
    for kind, phrases in (
        ("humanoid", HUMANOID_ZH),
        ("creature", CREATURE_ZH),
        ("mechanical", MECH_ZH),
        ("scene", SCENE_ZH),
        ("task_ui", TASK_UI_ZH),
        ("mention_ui", MENTION_UI_ZH),
    ):
        for phrase in _phrase_hits(blob, phrases):
            raw.append((kind, phrase))
    kept = _drop_shorter_inside_longer(raw)
    kinds = {k for k, _p in kept}

    covered = HUMANOID_ZH + MECH_ZH + SCENE_ZH + TASK_UI_ZH + MENTION_UI_ZH
    if _single_hit(blob, CREATURE_SINGLES, covered):
        kinds.add("creature")
    if tokens & HUMANOID_EN:
        kinds.add("humanoid")
    if tokens & CREATURE_EN:
        kinds.add("creature")
    if tokens & MECH_EN:
        kinds.add("mechanical")
    if tokens & SCENE_EN:
        kinds.add("scene")
    if tokens & TASK_UI_EN or any(p in blob for p in TASK_UI_PHRASES):
        kinds.add("task_ui")
    if tokens & MENTION_UI_EN:
        kinds.add("mention_ui")

    # portrait 单独不把宠物肖像改成「人加动物」。女人肖像仍是人物。
    humanoid_tokens = tokens & HUMANOID_EN
    if "creature" in kinds and humanoid_tokens <= {"portrait"} and "humanoid" in kinds:
        humanoid_phrases = [p for k, p in kept if k == "humanoid"]
        if not humanoid_phrases:
            kinds.discard("humanoid")
    # 无人机航拍是机位，不是机甲。机甲站在峡谷仍是机械。
    mech_phrases = {p for k, p in kept if k == "mechanical"}
    mech_tokens = tokens & MECH_EN
    camera_only = mech_phrases <= _CAMERA_PLATFORM_ZH and not mech_tokens
    if camera_only and ("scene" in kinds or "航拍" in blob):
        kinds.discard("mechanical")

    body = kinds & {"humanoid", "creature", "mechanical"}
    task_ui = "task_ui" in kinds
    if task_ui and not mod_l.startswith(("character.", "scene.")):
        return "ui"

    humanoid = "humanoid" in kinds
    creature = "creature" in kinds
    mechanical = "mechanical" in kinds
    if humanoid and creature:
        return "both"
    if humanoid and mechanical:
        return "humanoid"
    if creature:
        return "creature"
    if mechanical:
        return "mechanical"
    if humanoid:
        return "humanoid"

    mention_ui = "mention_ui" in kinds
    scene = "scene" in kinds or mod_l.startswith("scene.")
    if mention_ui and not scene and not body:
        return "ui"
    if scene:
        return "scene"
    if mod_l.startswith("character."):
        return "generic"
    return "unknown"


def floor_sentence(kind: str, lang: str = "en") -> str:
    row = FLOORS.get(kind) or {}
    if (lang or "en").lower().startswith("zh"):
        return row.get("zh") or ""
    return row.get("en") or ""


def clause(key: str, lang: str = "en", **fmt: str) -> str:
    row = REFLOW.get(key) or {}
    text = row.get("zh") if (lang or "en").lower().startswith("zh") else row.get("en")
    text = text or ""
    if fmt:
        try:
            text = text.format(**fmt)
        except (KeyError, IndexError):
            pass
    return text


def bilingual_pairs() -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for row in list(FLOORS.values()) + list(REFLOW.values()):
        zh, en = row.get("zh") or "", row.get("en") or ""
        if "{dir}" in zh or "{dir}" in en:
            continue
        if zh and en:
            pairs.append((zh, en))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def to_prompt_english(text: str) -> str:
    """Replace known Chinese clauses with the English twin. Unknown text stays."""
    out = text or ""
    for zh, en in bilingual_pairs():
        if zh in out:
            out = out.replace(zh, en)
    return out


def toy_medium_declared(*, goal: str = "", module: str = "", ref_analysis: Any = "") -> bool:
    if isinstance(ref_analysis, dict):
        ra = " ".join(str(v or "") for v in ref_analysis.values())
    else:
        ra = str(ref_analysis or "")
    blob = f"{goal or ''} {module or ''} {ra}".lower()
    return any(_affirmative_hit(blob, tok) for tok in _TOY_ALLOW)


def strip_foreign_medium_stubs(
    text: str,
    *,
    goal: str = "",
    module: str = "",
    ref_analysis: Any = "",
) -> tuple[str, list[str]]:
    """Drop toy-medium words unless the brief, module, or ref analysis declared that medium."""
    raw = text or ""
    if not raw.strip() or toy_medium_declared(goal=goal, module=module, ref_analysis=ref_analysis):
        return raw, []
    removed: list[str] = []

    def _sub(match: re.Match[str]) -> str:
        removed.append(match.group(0))
        return " "

    cleaned = raw
    for pat in _TOY_STUBS:
        cleaned = pat.sub(_sub, cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,，。；;|])", r"\1", cleaned)
    cleaned = re.sub(r"([,，；;|])\s*([,，；;|])+", r"\1", cleaned)
    return cleaned.strip(" |；;，,"), removed
