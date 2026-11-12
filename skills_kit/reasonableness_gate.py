"""出图前合理性闸门：提示词至少审核一次，并写出更合理的修订版。

对齐合成梯「先说通再出图」的成本模型：
- Agent 填清单 + 交 revised prompt
- CLI 做廉价启发式硬拦 + 写入会话
- converge generate 首轮无过闸则拒绝；过闸后默认注入 revised

不改动 ConvergeGate 的 9.5 / 满4轮 / 垫图规则；只把错误前提挡在 R1 之前。

逃生：须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`，可另加
`--skip-reasonableness-gate` / `PMEM_ART_SKIP_REASONABLENESS_GATE=1`
（仅调试；日常出图技能禁止跳过；仅设 SKIP 环境变量不够）。
"""
from __future__ import annotations

from .platform_cli import pmem_art_cli
import json
import re
import time
from pathlib import Path
from typing import Any

# skill id → 必检清单键（Agent 必须逐条标 ok/fail）
SKILL_CHECKLISTS: dict[str, tuple[str, ...]] = {
    "ordinary": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
    ),
    "keyart": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "hero_read",
        "layout_not_style_echo",
        "framing_lock",
    ),
    "clone": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "new_subject_not_ref_echo",
    ),
    "variant": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "only_named_delta",
    ),
    "split": (
        "subject_action",
        "contact_scale",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "role_separation",
        "state_machine",
    ),
    "shotpack": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "camera_sets_distinct",
    ),
    "ui": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "layout_zones",
        "no_content_clutter",
        "chrome_not_illustration",
        "cta_clear_of_faces",
        "control_craft",
    ),
    "icon.a": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "safe_zone",
        "single_symbol",
        "full_bleed_no_round_mask",
    ),
    "icon.b": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "stroke_consistency",
    ),
    "icon.c": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "silhouette_read",
        "transparent_friendly",
    ),
    "merge": (
        "subject_action",
        "element_budget",
        "hard_locks",
        "fail_at_glance",
        "single_centered_item",
        "chain_mode_declared",
        "upgrade_reason_concrete",
        "family_or_base_lock",
    ),
}

SKILL_ALIASES: dict[str, str] = {
    "draw": "ordinary",
    "普通图": "ordinary",
    "draw.ordinary": "ordinary",
    "原画": "keyart",
    "key-art": "keyart",
    "key_art": "keyart",
    "draw.key": "keyart",
    "keyart": "keyart",
    "克隆": "clone",
    "draw.clone": "clone",
    "变体": "variant",
    "draw.variant": "variant",
    "多图分工": "split",
    "多图": "split",
    "multi": "split",
    "multi-image": "split",
    "multi_image": "split",
    "draw.multi": "split",
    "镜头包": "shotpack",
    "镜头": "shotpack",
    "shot-pack": "shotpack",
    "shot_pack": "shotpack",
    "lens": "shotpack",
    "lenses": "shotpack",
    "draw.lens": "shotpack",
    "界面": "ui",
    "UI": "ui",
    "ui": "ui",
    "HUD": "ui",
    "hud": "ui",
    "uikit": "ui",
    "ui-kit": "ui",
    "ui_kit": "ui",
    "ui.kit": "ui",
    # 禁止裸 icon/图标 → icon.a；须显式 A/B/C
    "appicon": "icon.a",
    "app-icon": "icon.a",
    "app_icon": "icon.a",
    "icon_a": "icon.a",
    "icon-a": "icon.a",
    "图标a": "icon.a",
    "图标A": "icon.a",
    "桌面图标": "icon.a",
    "icon_b": "icon.b",
    "icon-b": "icon.b",
    "图标b": "icon.b",
    "图标B": "icon.b",
    "svg": "icon.b",
    "icon_c": "icon.c",
    "icon-c": "icon.c",
    "图标c": "icon.c",
    "图标C": "icon.c",
    "道具格": "icon.c",
    "合成梯": "merge",
    "合成": "merge",
    "merge-ladder": "merge",
    "merge_ladder": "merge",
    "merge.ladder": "merge",
    "overview": "merge",
    "overview_sheet": "merge",
    "per_cell": "merge",
    "整表": "merge",
    "一档一张": "merge",
}

# 裸「icon / 图标」不能默成 App Icon 或 ordinary
_AMBIGUOUS_ICON = frozenset({"icon", "图标", "图标集", "iconset", "icons"})

CHECK_LABELS_ZH: dict[str, str] = {
    "subject_action": "主体在做什么/交付物是什么",
    "contact_scale": "接触关系与相对尺度",
    "element_budget": "元素预算（不堆景不过载）",
    "hard_locks": "硬锁（画幅/透明底/无字/机位等）",
    "fail_at_glance": "一眼失败条件已写明",
    "hero_read": "主视觉记忆点一眼可读",
    "layout_not_style_echo": "只借画风不借样张构图/机位/分区",
    "new_subject_not_ref_echo": "新题材，不回声参考主体",
    "only_named_delta": "只改点名的差分项",
    "role_separation": "多图身份/结构分工不串",
    "camera_sets_distinct": "镜头套差异够大",
    "layout_zones": "界面分区清楚",
    "no_content_clutter": "内容区不塞插画杂物",
    "chrome_not_illustration": "控件壳来自 UI 规格，禁止叙事插画当垫图母版",
    "cta_clear_of_faces": "主 CTA 不遮脸/不压主角五官",
    "control_craft": "按钮/顶栏工艺（描边、体积、投影、字重）",
    "safe_zone": "72%–80% 安全区",
    "single_symbol": "单符号高识别",
    "full_bleed_no_round_mask": "满幅直角母版，禁止烤进圆角底板",
    "stroke_consistency": "线宽/端点一致",
    "silhouette_read": "厚剪影可读",
    "transparent_friendly": "底隔离友好（透明引擎真alpha / Cursor实色空底）",
    "single_centered_item": "每档单件居中",
    "parts_add_concrete": "（旧键，改用 upgrade_reason_concrete）零件增量具体可画",
    "base_body_retained": "（旧键，改用 family_or_base_lock）same_object 保留母体；shop 锁家族",
    "chain_mode_declared": "写清 same_object / shop_ladder / species_change / 轻门",
    "upgrade_reason_concrete": "升级理由具体（same_object→parts_add；shop/species→evolve_to+merge_why；轻门写具体可读升级）",
    "family_or_base_lock": "锁住母体或家族（same_object→母体词；shop/species→家族色相/题材；轻门→同任务域）",
    "sheet_safe_zone": "整表白卡/格内留边、主体不超框",
    "framing_lock": "景别硬锁写进修订句",
    "state_machine": "开关态逻辑自洽（铰链/解锁）",
}

_CROWD_RE = re.compile(
    r"(灯串|村庄|远景|近景|中景|前景|背景|粒子|特效|光晕|光柱|"
    r"雪花纹|碎花|满屏|堆满|层层叠叠|village|bokeh|god.?rays|"
    r"particle|ornament.?flood)",
    re.I,
)
_SAFE_ZONE_RE = re.compile(r"(安全区|safe.?zone|72\s*%|80\s*%|72%-80%|72%–80%)", re.I)
_ICON_SQUARE_RE = re.compile(r"(1\s*:\s*1|1024|正方形|square|满幅)", re.I)
_UI_ZONE_RE = re.compile(r"(九宫格|顶栏|底栏|内容区|面板|弹窗|HUD|9-?slice|panel)", re.I)
_TRANSPARENT_RE = re.compile(r"(透明|transparent|alpha)", re.I)
# Cursor 无 alpha 时用纯黑/实色隔离底；透明引擎仍写透明/alpha
_ISOLATION_BG_RE = re.compile(
    r"(透明|transparent|alpha|纯黑|黑底|实色隔离|隔离底|opaque\s*isolation|"
    r"solid\s*(black|isolation)|flat\s*black|#000000)",
    re.I,
)
_NO_TEXT_RE = re.compile(r"(无字|不要字|no\s*text|without\s*text|无可读)", re.I)
_SINGLE_ITEM_RE = re.compile(r"(单件|一件|居中|centered|single\s+item)", re.I)
_FULL_BLEED_RE = re.compile(
    r"(满幅直角|full[- ]?bleed|四角顶边|corners?\s+touch|无圆角蒙版|no\s*rounded\s*(mask|tile|plate))",
    re.I,
)
_ROUND_MASK_BAD_RE = re.compile(
    r"(圆角底板|圆角面板|rounded\s*(tile|squircle|plate|mask)|iOS\s*圆角蒙版烤进)",
    re.I,
)
_UI_CHROME_RE = re.compile(
    r"(顶栏|底栏|侧栏|主按钮|CTA|资源栏|九宫格|面板|bevel|描边|投影|字重|控件工艺|HUD)",
    re.I,
)
_UI_ILLUST_PAD_BAD_RE = re.compile(
    r"(叙事插画垫|气氛图垫|角色立绘垫|把插画当UI|插画当界面参考|茶会图垫|场景插画垫图|"
    r"叙事插画.{0,12}(垫|参考|母版)|气氛图.{0,12}(垫|参考|母版)|"
    r"茶会.{0,12}(庆祝|场景|插画|裁切).{0,16}(垫|参考|母版|主菜单|界面)|"
    r"插画裁切.{0,8}(UI|界面|主菜单)|插画当界面(参考|母版)|"
    r"把.{0,8}(插画|立绘|海报|茶会).{0,16}当.{0,16}(UI|界面|母版|主菜单)|"
    r"(立绘|插画海报).{0,8}(当|垫|做).{0,8}(界面|主菜单|UI|母版|图)|"
    r"插画海报垫(图)?|"
    r"(立绘|插画海报).{0,6}垫.{0,8}主菜单|"
    r"参考立绘.{0,8}(主菜单|界面)|拿插画当.{0,8}(主菜单|界面)母版|"
    r"场景插画垫图|"
    r"把立绘当界面参考)",
    re.I,
)
_CTA_FACE_RE = re.compile(
    r"(不遮脸|勿遮脸|避开面部|cta.?clear|never\s+cover\s+(the\s+)?face|主按钮不压脸)",
    re.I,
)
_CONTROL_CRAFT_RE = re.compile(r"(描边|投影|顶高光|体积|bevel|字重|inset|控件工艺)", re.I)
_FRAMING_RE = re.compile(
    r"(半身|胸像|上半身|全身|远景|中景|近景|特写|俯视|仰视|平视|腰以上|"
    r"bust|upper[- ]body|full[- ]body|bird'?s[- ]eye|low[- ]angle)",
    re.I,
)
_STATE_OPEN_RE = re.compile(r"(打开|开盖|开启|open(?:ed)?|unlocked)", re.I)
_STATE_OK_RE = re.compile(
    r"(铰链|hinge|解锁|打开态|移除挂锁|padlock\s+(open|removed|unlocked)|只改盖)",
    re.I,
)
_STATE_BAD_RE = re.compile(r"(闭合挂锁|锁着打开|closed\s+padlock.*open)", re.I)
_SOFT_CANDY_SUBJECT_RE = re.compile(
    r"(软糖|草莓糖|gummy|soft\s*candy)",
    re.I,
)
_SOFT_CANDY_MEDIA_RE = re.compile(
    r"(半透明|SSS|次表面|宽柔高光|translucen|subsurface|soft\s*gummy)",
    re.I,
)
_HARD_PLASTIC_ONLY_RE = re.compile(
    r"(硬塑胶|抛光塑料|树脂上漆|hard\s*plastic|lacquered\s*resin)",
    re.I,
)
# 不含裸「无/非」：避免「无字」把后面的肯定硬塑胶误判为已否定
_NEG_PREFIX_RE = re.compile(
    r"(禁止|不要|勿要|请勿|并非|不是|一眼失败|fail[- ]?at[- ]?glance|"
    r"(?:勿|别)(?=[硬烤圆]|硬塑|礼盒|奖杯|闭锁|挂锁|圆角))",
    re.I,
)


def _negated_before(text: str, at: int, span: int = 96) -> bool:
    start = max(0, int(at) - int(span))
    end = min(len(text), int(at) + 6)
    return bool(_NEG_PREFIX_RE.search(text[start:end]))


def normalize_skill(skill: str) -> str:
    raw = (skill or "").strip()
    if not raw:
        return "ordinary"
    key = raw.lower().replace(" ", "")
    if key in _AMBIGUOUS_ICON or raw in _AMBIGUOUS_ICON:
        return "icon.unspecified"
    if key in SKILL_CHECKLISTS:
        return key
    if raw in SKILL_ALIASES:
        return SKILL_ALIASES[raw]
    if key in SKILL_ALIASES:
        return SKILL_ALIASES[key]
    return key if key in SKILL_CHECKLISTS else "ordinary"


def default_checklist_template(skill: str) -> str:
    sk = normalize_skill(skill)
    keys = SKILL_CHECKLISTS.get(sk, SKILL_CHECKLISTS["ordinary"])
    return ";".join(f"{k}=ok" for k in keys)


def parse_checklist(text: str) -> dict[str, dict[str, str]]:
    """Parse `key=ok` / `key=fail:原因` / `key=ok:备注` 分号或换行分隔."""
    out: dict[str, dict[str, str]] = {}
    blob = (text or "").strip()
    if not blob:
        return out
    parts = re.split(r"[;\n]+", blob)
    for part in parts:
        piece = part.strip()
        if not piece or "=" not in piece:
            continue
        key, rest = piece.split("=", 1)
        key = key.strip()
        rest = rest.strip()
        if not key:
            continue
        if ":" in rest:
            status, note = rest.split(":", 1)
        else:
            status, note = rest, ""
        status_n = status.strip().lower()
        if status_n in ("ok", "pass", "true", "yes", "通过", "合理"):
            status_n = "ok"
        elif status_n in ("fail", "no", "false", "没过", "不合理", "bad"):
            status_n = "fail"
        else:
            status_n = "ok" if status_n == "" else "fail"
            note = rest
        out[key] = {"status": status_n, "note": note.strip()}
    return out


_L0_DIRECTION_SWAP = re.compile(
    r"(?:换成|改成|换做).{0,12}(?:题材|画风|风格|品类)|推倒重来|另起炉灶|"
    r"(?:改走|改成).{0,8}(?:合成梯|界面|图标|克隆)",
    re.I,
)
_L0_SKIP_CHUNKS = frozenset(
    {
        "必须写出",
        "禁止出现",
        "不要写成",
        "修订提示",
        "硬锁写进",
        "元素预算",
        "一眼失败",
        "安全区在",
        "满幅直角",
    }
)


def _l0_subject_drift(draft: str, revised: str) -> str:
    """If draft names clear subject chunks that revised drops, flag drift."""
    d = (draft or "").strip()
    r = (revised or "").strip()
    # CJK 一句约 8～10 字也够当主体锚；勿用英文词长门槛误放行
    if len(d) < 8 or len(r) < 8:
        return ""
    cjk_chunks = re.findall(r"[\u4e00-\u9fff]{3,6}", d)
    anchors: list[str] = []
    seen: set[str] = set()
    for ch in cjk_chunks:
        if ch in seen or ch in _L0_SKIP_CHUNKS:
            continue
        seen.add(ch)
        anchors.append(ch)
        if len(anchors) >= 3:
            break
    if anchors:
        missing = [a for a in anchors if a not in r]
        if len(missing) >= 2:
            return (
                "revised 疑似丢掉 draft 主体锚点（"
                + "、".join(missing[:3])
                + "）；合理性修订不得换题材"
            )
    if _L0_DIRECTION_SWAP.search(r) and not _L0_DIRECTION_SWAP.search(d):
        return "revised 新增换题材/换画风/换技能句；请回到原交付重审，勿借合理性闸换轨"
    return ""


def _heuristic_issues(skill: str, draft: str, revised: str, notes: str = "") -> list[str]:
    issues: list[str] = []
    d = (draft or "").strip()
    r = (revised or "").strip()
    n = (notes or "").strip()
    blob = f"{d}\n{r}\n{n}"
    if len(r) < 24:
        issues.append("revised 太短：修订提示词须写清主体、动作/布局与硬锁（至少约一句完整出图句）")
    if d and r and d == r and len(r) < 80:
        issues.append("revised 与 draft 完全相同且过短：请至少补上硬锁或元素预算，或把已合理处写完整")
    l0_msg = _l0_subject_drift(d, r)
    if l0_msg:
        issues.append(l0_msg)
    crowd_hits = _CROWD_RE.findall(r)
    if len(crowd_hits) >= 4 and not re.search(r"(只留|弱化|最多|减到|不要叠|预算)", r):
        issues.append(
            "元素预算可疑：修订句里堆景/特效词偏多且未写收敛预算（只留/弱化/最多…）"
        )
    if skill == "icon.a":
        if not _SAFE_ZONE_RE.search(r):
            issues.append("icon.a 缺安全区：修订句须含 72%–80% 安全区或 safe zone")
        if not _ICON_SQUARE_RE.search(r):
            issues.append("icon.a 缺画幅：修订句须点明 1:1 / 1024 / 满幅直角")
        if not _NO_TEXT_RE.search(r):
            issues.append("icon.a 缺无字：修订句须写死无字 / no text（母版禁止口号与小字）")
        if not _FULL_BLEED_RE.search(r):
            issues.append(
                "icon.a 缺满幅直角硬锁：修订句须写满幅直角/full-bleed/四角顶边，并禁止烤进圆角蒙版"
            )
        m_round = _ROUND_MASK_BAD_RE.search(r)
        if m_round and not _negated_before(r, m_round.start()):
            issues.append(
                "icon.a 禁止圆角底板：母版必须直角满幅；圆角由系统蒙版后加，不可烤进成图"
            )
    if skill == "icon.c" and not _ISOLATION_BG_RE.search(r):
        issues.append(
            "icon.c 缺底隔离：修订句须写纯黑/实色隔离底（Cursor）或透明底/transparent（透明引擎）；禁止后抠冒充 alpha"
        )
    if skill in {"ordinary", "keyart", "icon.c", "shotpack", "clone", "variant", "merge"} and _SOFT_CANDY_SUBJECT_RE.search(blob):
        if not _SOFT_CANDY_MEDIA_RE.search(r):
            issues.append(
                "软糖题材缺介质句：修订句须写半透明/SSS/宽柔高光/次表面，禁止只写题材名「软糖」或硬塑胶玩具"
            )
        m_hard = _HARD_PLASTIC_ONLY_RE.search(r)
        if m_hard and not _negated_before(r, m_hard.start()):
            issues.append("软糖题材勿把硬塑胶当目标介质：请改成软糖半透明并显式禁止硬塑胶")
    if skill == "ui":
        if not _UI_ZONE_RE.search(r):
            issues.append("ui 缺分区：修订句须点名九宫格/顶栏底栏/内容区/面板等")
        if _UI_ILLUST_PAD_BAD_RE.search(blob):
            issues.append(
                "ui 禁止叙事插画当垫图母版：主菜单须先写八项控件规格；真实截图只提炼文字，不垫插画/气氛图出控件"
            )
        if not _UI_CHROME_RE.search(r) or not _CONTROL_CRAFT_RE.search(r):
            issues.append(
                "ui 缺控件工艺：修订句须写顶栏/主按钮等分区，并写清描边/体积/投影/字重（对标商业休闲 HUD，不是插画海报）"
            )
        if not _CTA_FACE_RE.search(r):
            issues.append("ui 缺 CTA 避脸：修订句须写主按钮不遮脸/不压主角五官")
        if re.search(r"(巨型PLAY|超大Play|PLAY占半屏)", r, re.I) and not re.search(
            r"(禁止|不要|勿).{0,8}(巨型|超大)", r
        ):
            issues.append("ui CTA 体量过大：主按钮须克制，约占下三分之一宽，勿压死场景")
    if skill == "merge":
        if not _SINGLE_ITEM_RE.search(r):
            issues.append("merge 缺单件居中：修订句须写单件居中、非场景")
        has_named_mode = bool(re.search(
            r"(same_object|shop_ladder|species_change|同模加装|同族形变|换物种)",
            blob,
            re.I,
        ))
        light_gate = bool(re.search(r"轻门", blob))
        candyish = bool(re.search(r"(软糖|草莓糖|棒棒糖|糖纸|硬糖|gummy|soft\s*candy)", blob, re.I))
        # 非糖果可明示轻门；糖果必须显式 shop_ladder（「轻门」不能冒充）
        if candyish and not re.search(r"(shop_ladder|同族形变)", blob, re.I):
            issues.append(
                "merge 糖果链须点名 shop_ladder（同族形变）；禁止用轻门/same_object/省略冒充商业糖果升级"
            )
        elif not has_named_mode and not light_gate:
            issues.append(
                "merge 须点名 same_object / shop_ladder / species_change，或明示轻门（勿默认按同模加装填 parts_add）"
            )
        if re.search(r"(same_object|同模加装|同物件)", blob, re.I) and not re.search(
            r"(保留母体|母体词|同一草莓|同一软糖|base_body|每档.?仍?是.?同一|母体\+?零件|累计)",
            r,
            re.I,
        ):
            issues.append(
                "merge same_object 缺母体/累计：修订句须写死每档同一母体+零件累计（或明示替换式升级）"
            )
        if re.search(r"(shop_ladder|同族形变)", blob, re.I) and not re.search(
            r"(evolve_to|家族|色相|形变|包装|merge_why|合成理由)", r, re.I
        ):
            issues.append(
                "merge shop_ladder 缺形变理由：须写家族基因与 evolve/合成理由，禁止装饰换装断故事"
            )
        m_swap = re.search(r"(礼盒|奖杯|红宝石)", r)
        if (
            m_swap
            and re.search(r"(same_object|同物件|同模加装)", blob, re.I)
            and not _negated_before(r, m_swap.start())
        ):
            issues.append(
                "merge same_object 疑似换货：礼盒/奖杯作主语应改 shop_ladder 同族形变，或改成母体上的配件"
            )
    if skill == "split":
        if _STATE_OPEN_RE.search(blob):
            m_bad = _STATE_BAD_RE.search(r)
            if m_bad and not _negated_before(r, m_bad.start()):
                issues.append("split 打开态逻辑矛盾：开盖时不可同时保留闭合挂锁")
            if not _STATE_OK_RE.search(r):
                issues.append(
                    "split 打开态缺状态机：修订句须写铰链可见/挂锁解锁或移除/只改盖，禁止闭锁开盖"
                )
    if skill == "shotpack" and not re.search(
        r"(换机位|不同景别|俯|仰|侧|特写|远景|中景|机位差)", r
    ):
        issues.append(
            "镜头包缺机位差：点选后成图须相对普通棚拍正中改景别/高度/角度，禁止又一张同构图"
        )
    if skill == "clone" and re.search(r"(同一[个位]?人|原角色再画|抄回参考主体)", r):
        issues.append("clone 疑似回声参考主体：换题材锁画风，不要把参考人画回来")
    if skill == "keyart" and re.search(
        r"(照着样张构图|同机位照抄|贴样张分区|沿用参考构图|构图跟参考一样)",
        r,
    ):
        issues.append(
            "keyart 疑似 layout 回声：只借画风，修订句须写清新机位/新分区，禁止贴样张构图"
        )
    if skill == "keyart" and not re.search(
        r"(新机位|换机位|不借构图|不贴样张构图|layout_not_style_echo|只借色板|只借画风)",
        r,
        re.I,
    ):
        if re.search(r"(参考|样张|风格图|垫图)", r):
            issues.append(
                "keyart 缺 layout_not_style_echo：有样张时修订句须写明只借画风、新机位/不贴样张构图"
            )
    if skill == "keyart":
        if not _FRAMING_RE.search(r):
            issues.append(
                "keyart 缺景别硬锁：修订句须写半身/胸像/全身等可验收景别，并写一眼失败条件"
            )
        if re.search(r"半身|胸像|上半身|bust|upper[- ]body|腰以上", r, re.I):
            m_full = re.search(r"(全身群像|带狗|加狗|full[- ]body\s+crowd)", r, re.I)
            if m_full and not _negated_before(r, m_full.start()):
                issues.append("keyart 景别自相矛盾：既要半身又写全身群像/加狗，请删掉冲突句")
    return issues


def review_reasonableness(
    *,
    skill: str,
    draft: str,
    revised: str,
    checklist_text: str = "",
    notes: str = "",
    force_pass: bool = False,
) -> dict[str, Any]:
    """Return review payload. passed=False when checklist or heuristics fail."""
    sk = normalize_skill(skill)
    if sk == "icon.unspecified":
        return {
            "passed": False,
            "skill": sk,
            "skill_raw": (skill or "").strip(),
            "draft_prompt": (draft or "").strip(),
            "revised_prompt": (revised or "").strip(),
            "checklist": {},
            "issues": [
                "须点名 icon.a / icon.b / icon.c（或 图标A/B/C / SVG / 道具格），"
                "禁止裸 icon / 图标（会误当成普通图或一律 App Icon）"
            ],
            "notes": (notes or "").strip(),
            "force_pass": bool(force_pass),
            "reviewed_at": time.time(),
            "reviewed_at_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
    required = SKILL_CHECKLISTS.get(sk, SKILL_CHECKLISTS["ordinary"])
    parsed = parse_checklist(checklist_text)
    missing = [k for k in required if k not in parsed]
    failed_keys = [k for k, v in parsed.items() if k in required and v.get("status") != "ok"]
    heuristic = _heuristic_issues(sk, draft, revised, notes=notes)
    issues: list[str] = []
    if missing:
        issues.append(
            "清单未齐："
            + "、".join(f"{k}（{CHECK_LABELS_ZH.get(k, k)}）" for k in missing)
        )
    for k in failed_keys:
        note = (parsed.get(k) or {}).get("note") or ""
        label = CHECK_LABELS_ZH.get(k, k)
        issues.append(f"未过 {k}（{label}）" + (f"：{note}" if note else ""))
    if not force_pass:
        issues.extend(heuristic)
    elif len((revised or "").strip()) < 24:
        issues.append("即使 --force，revised 也不能为空壳")

    passed = len(issues) == 0
    checklist_out = {
        k: parsed.get(k) or {"status": "missing", "note": ""}
        for k in required
    }
    return {
        "passed": passed,
        "skill": sk,
        "skill_raw": (skill or "").strip(),
        "draft_prompt": (draft or "").strip(),
        "revised_prompt": (revised or "").strip(),
        "checklist": checklist_out,
        "issues": issues,
        "notes": (notes or "").strip(),
        "force_pass": bool(force_pass),
        "reviewed_at": time.time(),
        "reviewed_at_iso": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }


def apply_review_to_session(sess: dict[str, Any], review: dict[str, Any]) -> dict[str, Any]:
    """Persist review onto converge session dict (caller writes file)."""
    sess = dict(sess)
    history = list(sess.get("reasonableness_history") or [])
    history.append(
        {
            "reviewed_at": review.get("reviewed_at"),
            "passed": bool(review.get("passed")),
            "skill": review.get("skill"),
            "issues": list(review.get("issues") or []),
        }
    )
    sess["reasonableness_history"] = history[-8:]
    sess["reasonableness"] = {
        "passed": bool(review.get("passed")),
        "skill": review.get("skill"),
        "draft_prompt": review.get("draft_prompt"),
        "revised_prompt": review.get("revised_prompt"),
        "checklist": review.get("checklist"),
        "issues": list(review.get("issues") or []),
        "notes": review.get("notes") or "",
        "reviewed_at": review.get("reviewed_at"),
        "reviewed_at_iso": review.get("reviewed_at_iso"),
        "force_pass": bool(review.get("force_pass")),
        "skill_raw": review.get("skill_raw") or review.get("skill"),
    }
    notes = [d for d in list(sess.get("discussions") or []) if not (
        isinstance(d, dict) and d.get("kind") == "reasonableness"
    )]
    if review.get("passed"):
        chk = review.get("checklist") or {}
        ok_bits = [
            f"{k}=ok" + (f":{(chk[k] or {}).get('note')}" if (chk.get(k) or {}).get("note") else "")
            for k in chk
            if (chk.get(k) or {}).get("status") == "ok"
        ]
        notes.append(
            {
                "round": 0,
                "kind": "reasonableness",
                "prompt": str(review.get("revised_prompt") or ""),
                "strengths": "合理性闸已过：" + ("；".join(ok_bits) if ok_bits else "清单齐全"),
                "defects": "",
                "next_fix": "首轮 generate 使用本修订提示词；审美迭代不得推翻硬锁与元素预算",
            }
        )
    notes.sort(key=lambda d: int(d.get("round") or 0))
    sess["discussions"] = notes
    return sess


ROUTE_TO_REVIEW_SKILL = {
    "draw.ordinary": "ordinary",
    "draw.key": "keyart",
    "draw.clone": "clone",
    "draw.variant": "variant",
    "draw.multi": "split",
    "draw.lens": "shotpack",
    "ui.kit": "ui",
    "icon.a": "icon.a",
    "icon.b": "icon.b",
    "icon.c": "icon.c",
    "merge.ladder": "merge",
}


def _known_review_skill(skill: str) -> str:
    raw = (skill or "").strip()
    key = raw.lower().replace(" ", "")
    if key in SKILL_CHECKLISTS:
        return key
    if raw in SKILL_ALIASES:
        return str(SKILL_ALIASES[raw])
    if key in SKILL_ALIASES:
        return str(SKILL_ALIASES[key])
    return ""


def review_skill_matches_routes(skill: str, route_ids: list[Any] | None) -> bool:
    """会话记下了 route_ids 时，review 的 skill 必须落在其中。未知技能不能收成 ordinary。"""
    ids = [str(x) for x in (route_ids or []) if str(x)]
    if not ids:
        return True
    allowed = [ROUTE_TO_REVIEW_SKILL[r] for r in ids if r in ROUTE_TO_REVIEW_SKILL]
    if not allowed:
        return False
    known = _known_review_skill(skill)
    return bool(known) and known in allowed


def check_reasonableness_gate(
    sess: dict[str, Any],
    *,
    round_num: int = 1,
    prompt: str = "",
) -> tuple[bool, str, str]:
    """Return (ok, message, prompt_to_use).

    Any generate is blocked until the session has a passed reasonableness review
    (closes the ``--round 2`` skip loophole). Prompt injection of ``revised``
    only happens on the first generate; later rounds keep caller ``--prompt``
    (typically revised + next_fix).
    """
    del round_num  # round number must not decide whether the gate applies
    blob = sess.get("reasonableness") if isinstance(sess.get("reasonableness"), dict) else None
    if blob and blob.get("passed") and not review_skill_matches_routes(
        str(blob.get("skill_raw") or blob.get("skill") or ""),
        list(sess.get("route_ids") or []),
    ):
        return (
            False,
            "合理性 skill="
            + str(blob.get("skill") or "")
            + " 与本次路由 "
            + "、".join(str(x) for x in (sess.get("route_ids") or []))
            + " 不一致。请按这次 route 重跑 reasonableness review。",
            "",
        )
    if not blob or not blob.get("passed"):
        issues = ""
        if blob and blob.get("issues"):
            issues = " 上次未过：" + "；".join(str(x) for x in blob.get("issues")[:4])
        return (
            False,
            "出图前缺少已通过的合理性审核。请先：\n"
            f"  {pmem_art_cli()} reasonableness review --id <session> "
            "--skill <ordinary|keyart|clone|variant|split|ui|icon.a|icon.b|icon.c|merge> "
            "--draft \"<草稿提示词>\" --revised \"<更合理的提示词>\" "
            "--checklist \"subject_action=ok;contact_scale=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok\"\n"
            "审核须同时给出 revised；过闸后再 converge generate。"
            f"{issues}",
            "",
        )

    rounds = list(sess.get("rounds") or [])
    has_prior_image = any(str(r.get("image") or "").strip() for r in rounds)
    incoming = (prompt or "").strip()
    revised = str(blob.get("revised_prompt") or "").strip()
    draft = str(blob.get("draft_prompt") or "").strip()

    # Later rounds: keep caller prompt (usually revised + next_fix). Empty → fall back.
    if has_prior_image:
        if incoming:
            return True, "合理性闸已在本会话通过，沿用本轮 --prompt", incoming
        if revised:
            return True, "非首轮未给 --prompt，回退到合理性修订提示词", revised
        return True, "合理性闸已在本会话通过（无 revised 可回退）", incoming

    # First generate: ship reviewed revised only when caller agrees (or omits / repeats draft).
    # Never silently replace a different --prompt — that felt like irrational prompt mutation.
    if not revised:
        return (
            False,
            "合理性记录 passed 但 revised 为空，请重跑 reasonableness review。",
            "",
        )
    if not incoming or incoming == draft or incoming == revised:
        msg = "合理性闸已过，使用 revised" if incoming == revised else "已注入合理性修订提示词"
        return True, msg, revised
    return (
        False,
        "首轮 --prompt 与合理性 revised 不一致，已拒绝静默替换。"
        "请重跑 reasonableness review（把新提示词写入 --revised），"
        "或本轮 generate 省略 --prompt / 使用与 revised 相同的句子。",
        "",
    )


def format_review_print(review: dict[str, Any]) -> str:
    sk = review.get("skill")
    lines = [
        f"{'✅' if review.get('passed') else '❌'} [合理性闸 · {sk}] "
        f"{'通过' if review.get('passed') else '未通过'}",
    ]
    chk = review.get("checklist") or {}
    for k, v in chk.items():
        st = (v or {}).get("status") or "?"
        note = (v or {}).get("note") or ""
        mark = "✓" if st == "ok" else ("·" if st == "missing" else "✗")
        lines.append(f"  {mark} {k}（{CHECK_LABELS_ZH.get(k, k)}）{(' · ' + note) if note else ''}")
    for issue in review.get("issues") or []:
        lines.append(f"  · {issue}")
    if review.get("passed"):
        rev = str(review.get("revised_prompt") or "")
        lines.append("修订提示词（首轮 generate 须用这句；不一致会拒绝，不会静默盖掉）：")
        lines.append(rev if len(rev) <= 500 else rev[:500] + "…")
    else:
        lines.append("请按未过项改 revised / checklist 后重跑 review，禁止跳过直接 generate。")
    return "\n".join(lines)


def cmd_reasonableness_at_root(
    root: Path,
    *,
    action: str = "review",
    session_id: str = "latest",
    skill: str = "ordinary",
    draft: str = "",
    revised: str = "",
    checklist: str = "",
    notes: str = "",
    force: bool = False,
) -> int:
    from .converge import _session_file, _write_session_json

    action_n = (action or "review").strip().lower()
    sf = _session_file(root, session_id)
    if action_n == "show":
        if not sf.is_file():
            print(f"❌ 未找到会话 `{session_id}`")
            return 1
        sess = json.loads(sf.read_text(encoding="utf-8"))
        blob = sess.get("reasonableness")
        if not isinstance(blob, dict):
            print("尚无合理性审核记录。")
            return 1
        print(format_review_print({**blob, "passed": bool(blob.get("passed"))}))
        return 0 if blob.get("passed") else 1

    if action_n == "template":
        sk = normalize_skill(skill)
        print(f"skill={sk}")
        print(default_checklist_template(sk))
        for k in SKILL_CHECKLISTS.get(sk, SKILL_CHECKLISTS["ordinary"]):
            print(f"  - {k}: {CHECK_LABELS_ZH.get(k, k)}")
        return 0

    if action_n != "review":
        print("reasonableness 只支持 review | show | template")
        return 2

    if not sf.is_file():
        print(
            f"❌ 未找到收敛会话 `{session_id}`。请先 converge start，再跑合理性审核。\n"
            f"   {pmem_art_cli()} converge start --id {session_id} --goal ..."
        )
        return 1
    if not (revised or "").strip():
        print("❌ reasonableness review 需要 --revised（审核同时必须给出更合理的提示词）")
        return 1
    if not (draft or "").strip():
        print("❌ reasonableness review 需要 --draft（先写草稿，再给 revised）")
        return 1

    review = review_reasonableness(
        skill=skill,
        draft=draft,
        revised=revised,
        checklist_text=checklist,
        notes=notes,
        force_pass=force,
    )
    sess = json.loads(sf.read_text(encoding="utf-8"))
    # Always persist latest attempt (passed flag tells generate whether to unlock).
    sess = apply_review_to_session(sess, review)
    _write_session_json(sf, sess)
    print(format_review_print(review))
    if review.get("passed"):
        print(
            f"已写入会话 `{session_id}`。"
            "下一步用 revised 做 converge generate（可省略 --prompt，将自动注入）。"
        )
        return 0
    print("已写入会话（passed=false）；generate 仍会被拦截，请按未过项改 revised/checklist 后重跑 review。")
    return 1
