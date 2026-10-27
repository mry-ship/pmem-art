"""5D dimension parsing and score-inflation audit."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .prompt_scale import APP_ICON_DIM_WEIGHTS, DEFAULT_THRESHOLD, UI_DEDICATED_DIM_WEIGHTS

def _is_app_icon_5d_context(dims_str: str = "", module: str = "") -> bool:
    mod = (module or "").strip().lower()
    if mod in ("icon.appicon", "appicon", "app_icon") or mod.startswith("icon.app"):
        return True
    s = (dims_str or "").lower()
    icon_markers = ("识别度", "安全区", "圆角遮罩", "1024", "多尺寸", "色板纯粹", "appicon")
    return sum(1 for kw in icon_markers if kw in s) >= 2


def _is_ui_5d_context(dims_str: str = "", module: str = "") -> bool:
    mod = (module or "").strip().lower()
    if mod == "ui" or mod.startswith("ui."):
        return True
    s = (dims_str or "").lower()
    ui_markers = ("九宫格", "9-slice", "状态族", "套件", "透明底", "rgba", "合规")
    return sum(1 for kw in ui_markers if kw in s) >= 2


_CLAUSE_PUNCT = "，。；"
_CLAUSE_CLEAR = re.compile(
    r"已彻底解决|彻底解决|已解决|解决了|已修复|已消除|已去掉|不再出现|未出现|并未出现|并未发现|并非|严禁|禁止|不得出现|不得有"
)
_CLAUSE_STILL_BROKEN = re.compile(r"(?:没有|并未|还不|仍未|尚未|未|不)(?:彻底)?解决")
_LOCAL_NEGATORS = (
    "没有发生", "未出现", "未发现", "不存在", "并未", "并非", "不是",
    "没有", "不要", "别再", "never ", "without ", "not ", "no ",
    "非", "没", "无", "未", "不", "别",
)
_NEG_BOUNDARY = set("，。,.！!？?：:；;、…—（(）)[]「」\"'“” \n\t|/")


def _clause_text(text: str, index: int) -> str:
    start = 0
    for i, ch in enumerate(text[:index]):
        if ch in _CLAUSE_PUNCT:
            start = i + 1
    end = len(text)
    for i in range(index, len(text)):
        if text[i] in _CLAUSE_PUNCT:
            end = i
            break
    return text[start:end]


def _locally_negated(text: str, index: int) -> bool:
    """True when a negator sits immediately before index and is not part of another word."""
    window = text[max(0, index - 8):index]
    for neg in _LOCAL_NEGATORS:
        if not window.endswith(neg):
            continue
        neg_at = index - len(neg)
        prev = text[neg_at - 1] if neg_at else ""
        if len(neg) == 1 and prev and prev not in _NEG_BOUNDARY:
            continue
        if neg == "不是" and prev in {"岂", "无"}:
            continue
        if neg == "无" and prev == "不":
            continue
        return True
    return False


def _keyword_hits(text: str, keywords: tuple[str, ...]) -> list[str]:
    """Match keywords. A resolved or forbidden clause does not count, nor does a directly negated hit."""
    low = (text or "").lower()
    hits: list[str] = []
    for kw in keywords:
        k = kw.lower()
        start = 0
        while True:
            i = low.find(k, start)
            if i < 0:
                break
            clause = _clause_text(low, i)
            if _CLAUSE_CLEAR.search(clause) and not _CLAUSE_STILL_BROKEN.search(clause):
                start = i + len(k)
                continue
            if _locally_negated(low, i):
                start = i + len(k)
                continue
            hits.append(kw)
            break
    return hits


def _parse_kv_5d(dims_str: str, weights: dict[str, float]) -> dict[str, Any] | None:
    pairs = re.findall(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+(?:\.[0-9]+)?)",
        dims_str or "",
    )
    if len(pairs) < 4:
        return None
    bucket: dict[str, list[float]] = {}
    alias = {
        "composition": "composition",
        "comp": "composition",
        "lighting": "lighting_color",
        "light": "lighting_color",
        "color": "lighting_color",
        "perspective": "perspective_anatomy",
        "anatomy": "perspective_anatomy",
        "craft": "perspective_anatomy",
        "texture": "texture_detail",
        "detail": "texture_detail",
        "style": "spec_style",
        "spec": "perspective_anatomy",
    }
    saw_style = False
    for key, val in pairs:
        k = key.lower()
        if k == "style":
            saw_style = True
        dest = alias.get(k)
        if dest is None:
            continue
        if k == "spec" and not saw_style and "style" not in {p[0].lower() for p in pairs}:
            dest = "spec_style"
        bucket.setdefault(dest, []).append(float(val))
    parsed = {k: round(sum(v) / len(v), 2) for k, v in bucket.items()}
    needed = ("composition", "lighting_color", "perspective_anatomy", "texture_detail", "spec_style")
    if "lighting_color" not in parsed and all(k in parsed for k in ("composition", "perspective_anatomy", "texture_detail", "spec_style")):
        others = [parsed[k] for k in ("composition", "perspective_anatomy", "texture_detail", "spec_style")]
        parsed["lighting_color"] = round(sum(others) / len(others), 2)
    if any(k not in parsed for k in needed):
        return None
    weighted = sum(parsed[k] * weights.get(k, 0.2) for k in needed)
    return {"parsed": {k: parsed[k] for k in needed}, "weighted_score": round(weighted, 2), "rubric_mode": "general_5d"}


def _parse_skill_additive(dims_str: str) -> dict[str, Any] | None:
    """Skill rubric: 风格2.5 + 结构2.5 + 光影2.0 + 合规1.5 + 还原1.5, summed to 10.

    Values on the 10-point scale (e.g. 风格9.5/结构9.0/…) are normalized into the
    additive caps instead of failing open with a silent 0.
    """
    spec = (
        ("style_palette", r"(?:风格色板|风格|色板)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
        # 「构图叙事」等旧 concept 侧重标签：无「结构」时也可落入加和尺，避免 judge 记 0 分
        ("structure", r"(?:结构透视|构图叙事(?:与透视)?|结构|构图)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
        ("lighting_material", r"(?:光影材质|光影)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
        ("compliance", r"(?:管线与红线合规|红线合规|合规|红线)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
        ("intent", r"(?:氛围[/／]?意图还原|氛围意图还原|设定还原|氛围|还原|意图)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
    )
    # Require skill-only markers so general 「构图/透视/质感」 strings stay on general_5d.
    probe = dims_str or ""
    if not re.search(r"(?:合规|红线|还原|意图|氛围)", probe):
        return None
    if not re.search(r"(?:风格|色板)", probe) or not re.search(r"(?:结构|构图)", probe):
        return None
    # Absolute-5D 主串（含质感且无合规/红线类）留给 general_5d
    if re.search(r"(?:质感|肌理|细节|texture)", probe, flags=re.IGNORECASE) and not re.search(
        r"(?:合规|红线)", probe
    ):
        return None
    raw: dict[str, float] = {}
    for key, pat, _cap in spec:
        m = re.search(pat, probe)
        if not m:
            return None
        raw[key] = float(m.group(1))
    is_subscale = all(raw[k] <= cap + 0.05 for k, _, cap in ((s[0], None, s[2]) for s in spec))
    if not is_subscale:
        if any(raw[k] > 10.05 for k in raw):
            return None
        for key, _pat, cap in spec:
            raw[key] = round((raw[key] / 10.0) * cap, 2)
    else:
        for key, _pat, cap in spec:
            if raw[key] > cap + 0.05:
                return None
    total = round(sum(raw.values()), 2)
    return {"parsed": raw, "weighted_score": total, "rubric_mode": "skill_additive_5d"}


def parse_5d_dims(
    dims_str: str,
    weights: dict[str, float] | None = None,
    *,
    module: str = "",
) -> dict[str, Any]:
    """
    Parse a 5D score string and compute weighted score.
    Supports:
    1) General art / character / concept 5D: 构图 / 光影 / 透视 / 质感 / 风格 (leaves /pmem-draw untouched)
    2) Dedicated /pmem-ui 5D rubric when module starts with 'ui' or UI keywords are present:
       风格色板契合(25%) · 九宫格/结构(25%) · 光影材质(20%) · 透明底/RGBA管线合规(15%) · 套件状态族一致性(15%)
       Automatically normalizes 2.5/2.5/2.0/1.5/1.5 point scales or 10-point scales to /10.0.
    """
    import re as _re

    skill_hit = _parse_skill_additive(dims_str)
    if skill_hit is not None:
        return skill_hit

    w_preview = weights or {
        "composition": 0.20,
        "lighting_color": 0.25,
        "perspective_anatomy": 0.20,
        "texture_detail": 0.20,
        "spec_style": 0.15,
    }
    kv_hit = _parse_kv_5d(dims_str, w_preview if not weights else weights)
    if kv_hit is not None:
        return kv_hit

    if _is_app_icon_5d_context(dims_str, module=module):
        icon_patterns = {
            "glyph_silhouette": (r"(?:识别度|品牌符号|符号|小尺寸|glyph|silhouette)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "squircle_safe_zone": (r"(?:安全区|圆角遮罩|1024母版|母版|safe_zone|squircle)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "tactile_lighting": (r"(?:光影质感|微立体|光影|材质|tactile|lighting)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
            "multisize_adaptive": (r"(?:多尺寸合规|多尺寸|深浅色|自适应|multisize|adaptive)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
            "palette_purity": (r"(?:色板纯粹|无文字红线|色板|纯粹|palette|purity)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
        }
        icon_parsed: dict[str, float] = {}
        raw_vals_ic: dict[str, float] = {}
        for k, (pat, max_pt) in icon_patterns.items():
            m = _re.search(pat, dims_str or "", flags=_re.IGNORECASE)
            if m:
                raw_vals_ic[k] = float(m.group(1))
        if len(raw_vals_ic) == 5:
            is_subscale = all(raw_vals_ic[k] <= icon_patterns[k][1] + 0.05 for k in raw_vals_ic)
            for k, val in raw_vals_ic.items():
                max_pt = icon_patterns[k][1]
                icon_parsed[k] = round((val / max_pt) * 10.0, 2) if is_subscale else val
            ic_w = APP_ICON_DIM_WEIGHTS
            weighted = sum(icon_parsed[k] * ic_w[k] for k in icon_parsed)
            return {
                "parsed": icon_parsed,
                "weighted_score": round(weighted, 2),
                "rubric_mode": "app_icon_5d",
            }

    if _is_ui_5d_context(dims_str, module=module):
        ui_patterns = {
            "style_palette": (r"(?:风格色板|风格|色板|style_palette)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "nine_slice_structure": (r"(?:九宫格|9-slice|结构|nine_slice)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "lighting_material": (r"(?:光影材质|光影|材质|lighting_material)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
            "rgba_pipeline_compliance": (r"(?:透明底|rgba|管线合规|合规|红线|pipeline)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
            "state_suite_cohesion": (r"(?:状态族|套件一致性|套件|状态|一致性|还原|state_suite)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
        }
        ui_parsed: dict[str, float] = {}
        raw_vals: dict[str, float] = {}
        for k, (pat, max_pt) in ui_patterns.items():
            m = _re.search(pat, dims_str or "", flags=_re.IGNORECASE)
            if m:
                raw_vals[k] = float(m.group(1))
        if len(raw_vals) == 5:
            # Check if scored on sub-weights (<=2.5) vs 10-point scale
            is_subscale = all(raw_vals[k] <= ui_patterns[k][1] + 0.05 for k in raw_vals)
            for k, val in raw_vals.items():
                max_pt = ui_patterns[k][1]
                ui_parsed[k] = round((val / max_pt) * 10.0, 2) if is_subscale else val
            ui_w = UI_DEDICATED_DIM_WEIGHTS
            weighted = sum(ui_parsed[k] * ui_w[k] for k in ui_parsed)
            return {
                "parsed": ui_parsed,
                "weighted_score": round(weighted, 2),
                "rubric_mode": "ui_5d",
            }

    w = weights or {
        "composition": 0.20,
        "lighting_color": 0.25,
        "perspective_anatomy": 0.20,
        "texture_detail": 0.20,
        "spec_style": 0.15,
    }
    patterns = {
        "composition": r"(?:构图|composition)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "lighting_color": r"(?:光影|色彩|lighting)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "perspective_anatomy": r"(?:透视|解剖|结构|perspective|anatomy)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "texture_detail": r"(?:质感|肌理|细节|texture)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "spec_style": r"(?:风格|规格|spec|style)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
    }
    parsed: dict[str, float] = {}
    for k, pat in patterns.items():
        m = _re.search(pat, dims_str or "", flags=_re.IGNORECASE)
        if m:
            parsed[k] = float(m.group(1))
    if len(parsed) == 5:
        weighted = sum(parsed[k] * w.get(k, 0.2) for k in parsed)
        return {"parsed": parsed, "weighted_score": round(weighted, 2), "rubric_mode": "general_5d"}
    return {"parsed": parsed, "weighted_score": None, "rubric_mode": "general_5d"}


_SOFT_DEFECT_PHRASES: tuple[str, ...] = (
    "无明显硬伤",
    "没有明显硬伤",
    "无明显问题",
    "没有明显问题",
    "没有硬伤",
    "无缺陷",
    "无问题",
    "细节达标",
    "画面干净",
    "完成度高",
    "整体不错",
    "已经很好",
    "基本达标",
    "合格",
    "达标",
    "完美",
    "none",
    "n/a",
    "ok",
    "nil",
)
_SOFT_FILLER = re.compile(r"(基本|整体|大体|仍然|几乎|已经|非常|比较|很)")


def defects_are_substantive(defects_str: str) -> bool:
    """False when defects are empty or only rubber-stamp / praise phrases (cannot justify a 9.6 stop)."""
    raw = (defects_str or "").strip()
    if len(raw) < 4:
        return False
    clauses = [c.strip() for c in re.split(r"[；;\|/\n]+", raw) if c.strip()]
    if not clauses:
        return False
    substantive = 0
    for clause in clauses:
        cleaned = clause
        # Longer soft phrases first so 「无明显硬伤」wins over bare 「无」.
        for tok in sorted(_SOFT_DEFECT_PHRASES, key=len, reverse=True):
            cleaned = re.sub(re.escape(tok), " ", cleaned, flags=re.IGNORECASE)
        cleaned = _SOFT_FILLER.sub(" ", cleaned)
        cleaned = re.sub(r"[\s　。.!！,，、：:]+", "", cleaned)
        if cleaned in ("", "无"):
            continue
        if len(cleaned) >= 2:
            substantive += 1
    return substantive > 0


def audit_score_inflation(
    raw_score: float,
    dims_str: str,
    defects_str: str,
    prev_score: float | None,
    scale_prof: dict[str, Any],
    round_num: int = 1,
    module: str = "",
) -> dict[str, Any]:
    """
    Reverse-analysis guardrail: when five dimensions parse, the weighted score is the score.
    A hand-filled total is never kept above or instead of that weighted score.
    Unparsed dimensions do not fall back to a hand-filled total.
    """
    w_info = parse_5d_dims(dims_str, scale_prof.get("dim_weights"), module=module)
    weighted = w_info.get("weighted_score")
    warnings: list[str] = []
    if weighted is not None:
        if raw_score is not None and float(raw_score) > 0 and abs(float(raw_score) - float(weighted)) > 0.05:
            if float(raw_score) > float(weighted):
                warnings.append(
                    f"检测到报送总分 ({float(raw_score):.2f}) 高于五维加权计算分 ({float(weighted):.2f})，已改用五维加权分"
                )
        calibrated = float(weighted)
    else:
        if raw_score is not None and float(raw_score) > 0:
            warnings.append("五维字符串无法解析，拒绝采用手填总分，本轮记 0 分")
        calibrated = 0.0

    limb_artifact_keywords = (
        "三只手", "多手", "第三只手", "多余的手", "多指", "六指", "多余肢体", "三条腿", "三条手臂", "三只胳膊",
        "多出一条", "多余刀鞘", "多余武器", "解剖错误", "肢体畸形", "手部畸形",
        "three hands", "3 hands", "extra hand", "extra hands", "extra limb", "extra limbs",
        "three arms", "3 arms", "extra arm", "mutated hand", "extra fingers", "fused fingers",
        "anatomical artifact", "extra weapon", "extra sheath",
    )
    defects_lower = (defects_str or "").lower()
    hit_limb = _keyword_hits(defects_lower, limb_artifact_keywords)
    if hit_limb:
        warnings.append(
            f"解剖/肢体硬伤一票否决拦截：检测到多手/多肢体/多余器物伪影 {hit_limb}，强制触发硬伤上限压分 (<=7.90) 并拒绝达标"
        )
        calibrated = min(calibrated, 7.90)

    severe_defect_keywords = (
        "缺乏飞白",
        "数字化噪点",
        "数字化痕迹",
        "数字化滤镜",
        "数字化",
        "照搬",
        "呆板",
        "平光",
        "无明显变化",
        "颗粒太均匀",
        "画幅比例错误",
        "aspect ratio mismatch",
    )
    hit_kw = _keyword_hits(defects_lower, severe_defect_keywords)
    if hit_kw and calibrated > 9.0:
        warnings.append(
            f"反虚高拦截：缺陷栏包含关键短板词 {hit_kw}，禁止因基础完成度达标而给 9.0+ 虚高分，已触发严苛上限校准 (<=8.90)"
        )
        calibrated = min(calibrated, 8.90)

    # high / recompose / bold: do not reward dull photocopies of the ref.
    scale_name = str(scale_prof.get("scale") or "").strip().lower()
    photocopy_keywords = (
        "贴原", "闷贴", "复印", "过度还原", "机位未变", "几乎没换机位",
        "冷暖分离不足", "对比度不足", "戏剧光不足", "平光证件照",
        "photocopy", "too close to reference", "near-duplicate",
    )
    if scale_name in ("high", "recompose") and calibrated > 9.0:
        hit_photo = _keyword_hits(defects_str or "", photocopy_keywords)
        if hit_photo:
            warnings.append(
                f"反贴原拦截（{scale_name}）：检测到 {hit_photo}，禁止因「长得像原图」虚高，压分 (<=8.85)"
            )
            calibrated = min(calibrated, 8.85)
        # Dims-only cue: high composition + weak lighting = photocopy-shaped score.
        parsed = w_info.get("parsed") or {}
        try:
            comp = float(parsed.get("composition") or 0)
            light = float(parsed.get("lighting_color") or 0)
        except (TypeError, ValueError):
            comp, light = 0.0, 0.0
        if scale_name == "high" and comp >= 9.5 and 0 < light <= 8.6 and calibrated > 9.0:
            warnings.append(
                "反贴原拦截（high）：构图≥9.5 且光影≤8.6，疑闷贴原图，压分 (<=8.95)"
            )
            calibrated = min(calibrated, 8.95)

    if scale_prof.get("allow_action_pose_change") is False:
        pose_drift_keywords = (
            "动作改变", "姿态改变", "动作不符", "姿态不符", "姿态偏移", "动作偏移",
            "改为托腮", "变成托腮", "改成抱膝",
            "pose changed", "action changed", "pose drift",
        )
        hit_pose = _keyword_hits(defects_str or "", pose_drift_keywords)
        if hit_pose:
            warnings.append(
                f"动作红线拦截：检测到角色动作/姿态偏移 {hit_pose}，强制压分 (<=8.50) 并拒绝达标"
            )
            calibrated = min(calibrated, 8.50)

    scope_groups = []
    if scale_prof.get("allow_viewpoint_change") is False:
        scope_groups.append((
            "机位",
            ("改了机位", "改机位", "换了机位", "换了视角", "机位改变", "视角改变", "改了视角"),
        ))
    if scale_prof.get("allow_element_count_change") is False:
        scope_groups.append((
            "元素数量",
            ("增删元素", "元素数量改变", "多画了主体", "多画了一个", "少画了主体", "新增了主体", "删掉了主体"),
        ))
    if scale_prof.get("allow_layout_change") is False:
        scope_groups.append((
            "布局",
            ("改了布局", "布局改变", "重排了构图", "构图重排"),
        ))
    scope_groups.append((
        "身份",
        ("性别改变", "性别不符", "换成男性", "换成女性", "物种改变", "物种不符", "换了一张脸", "换脸", "年龄段变了", "年龄段不符"),
    ))
    for scope_name, scope_kws in scope_groups:
        hit_scope = _keyword_hits(defects_str or "", scope_kws)
        if hit_scope:
            warnings.append(
                f"{scope_name}红线拦截：检测到 {hit_scope}，强制压分 (<=8.50) 并拒绝达标"
            )
            calibrated = min(calibrated, 8.50)

    target_th = float(scale_prof.get("target_score_threshold", DEFAULT_THRESHOLD))
    min_leap = float(scale_prof.get("min_round_leap", 0.30))
    stagnated = False
    if prev_score is not None and prev_score > 0:
        delta = round(calibrated - prev_score, 2)
        if delta < min_leap and calibrated < target_th:
            stagnated = True
            scale_name = str(scale_prof.get("scale") or "").strip().lower()
            if scale_name == "low":
                advice = "下一轮只改缺陷部位；若原图离 9.6 远，换 medium 或 high"
            elif scale_name == "high":
                advice = "下一轮加强机位或戏剧光影，不要只改局部笔触"
            elif scale_name == "recompose":
                advice = "下一轮更贴近指定构图方向"
            else:
                advice = "下一轮在原构图内加强光影与材质，不要改机位或增删主体"
            warnings.append(
                f"收敛停滞预警：本轮净增 +{delta:.2f} 低于当前档位 ({scale_name or scale_prof.get('scale')}) "
                f"的最小跃升 +{min_leap:.2f}。{advice}"
            )

    return {
        "raw_score": round(float(raw_score if raw_score is not None and float(raw_score) > 0 else calibrated), 2),
        "calibrated_score": round(calibrated, 2),
        "dims_parsed": w_info.get("parsed", {}),
        "rubric_mode": w_info.get("rubric_mode") or "",
        "weighted_score": weighted,
        "stagnated": stagnated,
        "warnings": warnings,
    }



