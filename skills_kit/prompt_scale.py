"""Converge scale profiles and prompt directive helpers."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

DEFAULT_THRESHOLD = 9.6
DEFAULT_MAX_ROUNDS = 8
FAST_SOFT_THRESHOLD = 9.0  # fast-track: prefer fewer regens when score>=9.0 & delta small; final accept still >=9.6 unless draft
# Physical image gate: solid-gray probes sit ~2.5–2.9; real art JPEGs are typically ≥6.
MIN_IMAGE_BYTE_ENTROPY = 3.2
MIN_IMAGE_EDGE_PX = 64

CONVERGE_SCALE_PROFILES: dict[str, dict[str, Any]] = {
    "low": {
        "scale": "low",
        "label": "低强度 · 保守修瑕动态达标闭环 (Defect-Fix Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.15,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.25,
            "texture_detail": 0.25,
            "spec_style": 0.15,
        },
        "next_fix_budget": "conservative (~15% prompt delta, <=20%)",
        "max_prompt_delta_ratio": 0.20,
        "allow_recompose": False,
        "allow_viewpoint_change": False,
        "allow_action_pose_change": False,
        "allow_element_count_change": False,
        "allow_layout_change": False,
        "allow_lighting_overhaul": False,
        "forbidden_changes": [
            "viewpoint_angle (不改机位与镜头视角)",
            "character_action_and_pose (不改动作与姿态)",
            "element_count (不增删主体元素)",
            "scene_layout (不改场景布局)",
            "style_medium (保持原图画风笔触与色板)",
            "identity_lock (保持原图性别、物种、年龄段与核心外观)",
        ],
        "min_round_leap": 0.12,
        "prompt_delta_baseline": "first",
        "prompt_directive": "原图画风优先：锁视角与姿态，仅微调局部笔触",
    },
    "medium": {
        "scale": "medium",
        "label": "中强度 · 补足加小优化动态达标闭环 (Balance & Polish Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.20,
            "lighting_color": 0.25,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.20,
            "spec_style": 0.15,
        },
        "next_fix_budget": "moderate (~35% prompt delta, <=45%; cumulative <=60% vs first)",
        "max_prompt_delta_ratio": 0.45,
        "max_prompt_delta_vs_first": 0.60,
        "allow_recompose": False,
        "allow_viewpoint_change": False,
        "allow_action_pose_change": False,
        "allow_element_count_change": False,
        "allow_layout_change": False,
        "allow_lighting_overhaul": True,
        "forbidden_changes": [
            "viewpoint_angle (不改机位与镜头视角)",
            "character_action_and_pose (不改动作与姿态)",
            "element_count (不增删主体元素)",
            "scene_layout (不重排画面布局)",
            "style_medium (保持原图画风笔触与色板)",
            "identity_lock (保持原图性别、物种、年龄段与核心外观)",
        ],
        "min_round_leap": 0.22,
        "prompt_delta_baseline": "previous",
        # Stub only — NOT the live contract. get_converge_scale_profile always overwrites
        # via build_dynamic_prompt_directive (painterly may inject SSS; UI/pixel/flat skip it).
        # Do not put 次表面散射 here: reading the table would falsely imply every medium run gets SSS.
        "prompt_directive": (
            "【收敛强度: MEDIUM (补足加小优化)】保持原图核心画风、机位、姿态与主体，"
            "按媒介补光影与材质"
        ),
    },
    "high": {
        "scale": "high",
        "label": "高强度 · 大胆重构光影与张力动态达标闭环 (Showcase Overhaul Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.20,
            "lighting_color": 0.25,
            "perspective_anatomy": 0.15,
            "texture_detail": 0.20,
            "spec_style": 0.20,
        },
        "next_fix_budget": "bold_overhaul (~65% prompt delta, <=70%; cumulative <=85% vs first)",
        "max_prompt_delta_ratio": 0.70,
        "max_prompt_delta_vs_first": 0.85,
        "allow_recompose": False,
        "allow_viewpoint_change": True,
        "allow_action_pose_change": True,
        "allow_element_count_change": False,
        "allow_layout_change": True,
        "allow_lighting_overhaul": True,
        "forbidden_changes": [
            "style_medium (保持原图核心艺术媒介与画风基因)",
            "identity_lock (保持原图性别、物种、年龄段与核心外观)",
            "no_foreign_props (叙事道具只保留原图已有主体)",
        ],
        "min_round_leap": 0.30,
        "prompt_delta_baseline": "previous",
        # Fallback only — runtime rebuilds; keep Showcase clauses in sync with dynamic builder.
        "prompt_directive": (
            "【收敛强度: HIGH (Showcase级大胆跃升)】严禁停留在小修小补或平庸平移！"
            "在锁定原图核心艺术媒介与角色身份的前提下，升级电影级镜头张力与高反差冷暖戏剧光影；"
            "叙事道具只沿用原图已有主体"
        ),
    },
    "recompose": {
        "scale": "recompose",
        "label": "定向改构图模式 · 按用户指定新构图动态达标闭环 (Directed Re-Composition Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.30,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.15,
            "spec_style": 0.15,
        },
        "next_fix_budget": "directed_recompose (~80% prompt delta, <=85%; cumulative <=95% vs first)",
        "max_prompt_delta_ratio": 0.85,
        "max_prompt_delta_vs_first": 0.95,
        "allow_recompose": True,
        "allow_viewpoint_change": True,
        "allow_action_pose_change": True,
        "allow_element_count_change": False,
        "allow_layout_change": True,
        "allow_lighting_overhaul": True,
        "forbidden_changes": [
            "style_medium (保持原图画风笔触与色板)",
            "identity_lock (保持原图性别、物种、年龄段与核心外观)",
            "recompose_direction (不偏离指定构图方向)",
        ],
        "prompt_delta_baseline": "previous",
        # Match high leap so the intensity ladder is not inverted (recompose is orthogonal
        # via --recompose-dir, not a weaker leap bar).
        "min_round_leap": 0.30,
        "prompt_directive": "原图画风优先：承笔触色板，按指令重构构图",
    },
}


UI_DEDICATED_DIM_WEIGHTS: dict[str, float] = {
    "style_palette": 0.25,
    "nine_slice_structure": 0.25,
    "lighting_material": 0.20,
    "rgba_pipeline_compliance": 0.15,
    "state_suite_cohesion": 0.15,
}

APP_ICON_DIM_WEIGHTS: dict[str, float] = {
    "glyph_silhouette": 0.25,
    "squircle_safe_zone": 0.25,
    "tactile_lighting": 0.20,
    "multisize_adaptive": 0.15,
    "palette_purity": 0.15,
}



_CASE_ID_STYLE: dict[str, tuple[str, bool, list[str]]] = {
    "Case 01": (
        "仙侠水墨夜色风",
        True,
        [
            "low_angle_back_pose (不改男侠背影站位与俯瞰构图)",
            "pavilion_and_lantern_layout (严禁增删飞檐楼阁与暖金灯笼布局)",
            "male_swordsman_identity (保持原图男性持剑侠客身份，禁止改成女侠)",
        ],
    ),
    "Case 02": (
        "粉彩速写轻盈风",
        True,
        [
            "viewpoint_and_sitting_pose (严禁改变坐姿与镜头视角)",
            "pastel_sketch_medium_and_whitespace (严禁改变粉彩速写干爽笔触与米白纸留白)",
            "element_count (严禁增删主体元素或涂黑背景)",
        ],
    ),
    "Case 03": (
        "胶片逆光轻厚涂",
        True,
        [
            "frontal_bust_viewpoint (严禁改变正面胸像视角与二分光影)",
            "element_count_and_daisy_wallpaper (严禁增删人物或改变雏菊壁纸背景)",
        ],
    ),
    "Case 04": (
        "奇幻厚涂概念风",
        False,
        [
            "top_down_canyon_viewpoint (严禁改变垂直俯视天井视角)",
            "dragon_and_arch_layout (严禁增删左上绿龙与右侧雕花石拱门)",
        ],
    ),
}


def _match_style_keywords(blob: str, *, allow_weak_sketch: bool) -> tuple[str, bool, list[str]] | None:
    """Keyword style match. Weak tokens like bare 'sketch' only when allow_weak_sketch (ref path)."""
    b = (blob or "").lower()
    if not b.strip():
        return None
    pastel_keys = ("油画棒", "粉彩", "彩铅", "pastel", "crayon", "pastel_sketch")
    if allow_weak_sketch:
        pastel_keys = pastel_keys + ("速写", "sketch")
    if any(k in b for k in pastel_keys):
        return _CASE_ID_STYLE["Case 02"]
    if any(k in b for k in ("仙侠", "不夜城", "男侠", "女侠", "飞檐", "night_city", "celestial")):
        return _CASE_ID_STYLE["Case 01"]
    if any(k in b for k in ("峡谷", "天井", "绿龙", "石拱门", "canyon", "ishtar", "alley")):
        return _CASE_ID_STYLE["Case 04"]
    if any(k in b for k in ("逆光", "肖像", "胶片", "雏菊", "sunlit", "portrait")):
        return _CASE_ID_STYLE["Case 03"]
    if any(k in b for k in ("浮世绘", "ukiyoe")):
        return (
            "传统木版浮世绘",
            True,
            ["ukiyoe_woodblock_line_and_layout (严禁改变木版画平涂墨线与构图布局)"],
        )
    if any(k in b for k in ("植物", "玫瑰", "botanical", "rose")):
        return (
            "古典水彩植物志",
            False,
            ["botanical_parchment_and_layout (严禁改变羊皮纸留白与标本构图)"],
        )
    return None


def _infer_case_style_and_subject(
    goal: str = "",
    ref_analysis: str = "",
    ref_image: str = "",
    module: str = "",
) -> tuple[str, bool, list[str]]:
    """Infer style lead-in / case redlines. Prefer explicit ref/case id over loose goal keywords."""
    from .image_gates import resolve_case_config

    def _copy_hit(hit: tuple[str, bool, list[str]]) -> tuple[str, bool, list[str]]:
        return hit[0], hit[1], list(hit[2])

    cfg = resolve_case_config("", ref_image or "")
    if cfg and cfg.get("case_id") in _CASE_ID_STYLE:
        return _copy_hit(_CASE_ID_STYLE[str(cfg["case_id"])])

    # Ref path alone (may include weak tokens like pastel_sketch); do not mix goal yet.
    ref_hit = _match_style_keywords(ref_image or "", allow_weak_sketch=True)
    if ref_hit is not None:
        return _copy_hit(ref_hit)

    # Goal / analysis: stronger tokens only — bare "sketch" must not hijack a night-city brief.
    prose_hit = _match_style_keywords(
        f"{goal or ''} {ref_analysis or ''} {module or ''}",
        allow_weak_sketch=False,
    )
    if prose_hit is not None:
        return _copy_hit(prose_hit)

    blob = f"{goal or ''} {ref_analysis or ''} {ref_image or ''} {module or ''}".lower()
    has_char = not (str(module or "").startswith("scene.") and not any(k in blob for k in ("人物", "少女", "女侠", "男侠", "角色")))
    style_head = "原图画风优先"
    case_redlines = (
        [
            "viewpoint_angle (严禁改变机位视角)",
            "character_action_and_pose (严禁改变角色核心动作与姿态)",
            "style_medium (严禁背离原图画风笔触与色板)",
        ]
        if has_char
        else [
            "viewpoint_angle (严禁改变机位视角)",
            "scene_layout_and_elements (严禁改变场景布局与主体元素数量)",
            "style_medium (严禁背离原图画风笔触与色板)",
        ]
    )
    return style_head, has_char, case_redlines


def build_dynamic_prompt_directive(
    scale: str = "medium",
    *,
    goal: str = "",
    ref_analysis: str = "",
    ref_image: str = "",
    module: str = "",
    recompose_dir: str = "",
) -> str:
    """Dynamically generate scale-appropriate prompt_directive: low locks viewpoint/pose, medium polishes lighting & atmosphere, high encourages cinematic composition upgrades, narrative props & dynamic details."""
    s = (scale or "medium").strip().lower()
    style_head, has_char, _ = _infer_case_style_and_subject(
        goal=goal, ref_analysis=ref_analysis, ref_image=ref_image, module=module
    )
    if s == "low":
        body = "锁视角与姿态，仅微调局部笔触" if has_char else "锁视角与布局，仅微调局部笔触"
        return f"{style_head}：{body}"
    if s == "medium":
        blob = f"{style_head} {goal}"
        mod_l = (module or "").strip().lower()
        # UI / pixel / icon kits: SSS reads as soft skin shading and pollutes flat graphic looks.
        no_sss = (
            mod_l == "ui"
            or mod_l.startswith("ui.")
            or mod_l.startswith("icon.")
            or "pixel" in mod_l
            or any(k in blob.lower() for k in ("像素", "pixel", "ui kit", "九宫格", "hud"))
        )
        if no_sss:
            light = "加强清晰色块边界、状态对比与材质可读性"
        elif any(k in blob for k in ("速写", "粉彩", "水彩", "浮世绘", "水墨", "线稿", "pastel", "sketch", "ukiyoe")):
            light = "加强侧逆光、留白层次与媒介笔触"
        else:
            light = "加强侧逆光、次表面散射、环境反射与物理媒介质感"
        return (
            f"{style_head}：【收敛强度: MEDIUM (补足加小优化)】保持原图核心画风、机位、姿态与主体，"
            f"{light}"
        )
    if s == "high":
        return (
            f"{style_head}：【收敛强度: HIGH (Showcase级大胆跃升)】严禁停留在小修小补或平庸平移！"
            "在锁定原图核心艺术媒介与角色身份（性别、物种、年龄段、核心外观）的前提下，"
            "升级电影级镜头张力与高反差冷暖戏剧光影（体积光、斑驳光斑、冷暖交界）；"
            "叙事道具只沿用原图已有主体，禁止搬入原图没有的物件"
        )
    return (
        f"{style_head}：【收敛强度: RECOMPOSE (定向改构图)】严格继承参考原图的画风笔触、媒介肌理与主辅色板，"
        f"100% 按照指定构图改造方向（{recompose_dir or '指定新机位与景别'}）重排镜头机位、主体位置与空间景深层次"
    )


def _forbidden_families(item: str) -> set[str]:
    """Map a forbidden/case-redline clause to semantic families for low-scale dedup."""
    raw = str(item or "")
    key = raw.split("(", 1)[0].strip().lower()
    body = raw.lower()
    families: set[str] = set()
    if any(t in key for t in ("viewpoint", "angle", "canyon_viewpoint", "bust_viewpoint")) or any(
        t in body for t in ("机位", "视角", "俯瞰", "viewpoint", "angle")
    ):
        families.add("viewpoint")
    if any(t in key for t in ("pose", "action", "sitting")) or any(
        t in body for t in ("姿态", "动作", "站位", "坐姿", "pose", "action")
    ):
        families.add("pose")
    if any(t in key for t in ("element",)) or any(t in body for t in ("增删", "元素数量", "主体元素")):
        families.add("element")
    if any(t in key for t in ("layout", "pavilion", "lantern", "wallpaper", "daisy")) or any(
        t in body for t in ("布局", "layout")
    ):
        families.add("layout")
    if any(t in key for t in ("style", "medium", "pastel_sketch", "ukiyoe", "botanical")) or any(
        t in body for t in ("画风", "笔触", "色板", "媒介")
    ):
        families.add("style")
    if "identity" in key or any(t in body for t in ("性别", "物种", "年龄段", "核心外观")):
        families.add("identity")
    if "recompose" in key:
        families.add("recompose")
    if "foreign" in key or "props" in key or "物件" in body:
        families.add("props")
    return families or {key or raw}


def _merge_low_forbidden(base: list[str], case_redlines: list[str]) -> list[str]:
    """Prefer case-specific redlines over generic same-family base clauses; avoid stacking duplicates."""
    if not case_redlines:
        return list(base)
    case_fams: set[str] = set()
    for item in case_redlines:
        case_fams |= _forbidden_families(item)
    merged = [m for m in base if not (_forbidden_families(m) & case_fams)]
    for item in case_redlines:
        if item not in merged:
            merged.append(item)
    return merged


def strip_redline_tags_from_generation_text(text: str) -> str:
    """Ensure [红线锁死: ...] headers never appear in generation prompt or next_fix."""
    if not text:
        return ""
    cleaned = re.sub(r"\[红线锁死:\s*[^\]]*\]\s*", "", str(text))
    return cleaned.strip(" |")


def _body_without_scale_banner(text: str, directive: str = "") -> str:
    """Drop the scale banner words, keep the rest of the prompt for diffing and reuse."""
    raw = text or ""
    if directive:
        raw = raw.replace(directive, " ")
    banner = re.compile(r"【收敛强度:[^】]*】|仅微调局部笔触|定向改构图|Showcase级(?:大胆跃升)?")
    kept: list[str] = []
    for part in raw.split("|"):
        piece = banner.sub(" ", part)
        piece = re.sub(r"\s+", " ", piece).strip(" ：:，,")
        if not piece or piece.startswith("约束"):
            continue
        kept.append(piece)
    return " | ".join(kept)


def _constraint_tail(scale_prof: dict[str, Any]) -> str:
    """Redlines stay at the end of the generation prompt, after style and subject."""
    clauses: list[str] = []
    for item in scale_prof.get("forbidden_changes") or []:
        text = str(item).strip()
        if text.endswith(")") and "(" in text:
            text = text[text.rfind("(") + 1:-1].strip()
        if text and text not in clauses:
            clauses.append(text)
    if not clauses:
        return ""
    return "约束：" + "；".join(clauses)


def _prompt_change_ratio(prev: str, curr: str, directive: str = "") -> float:
    import difflib
    a = _body_without_scale_banner(prev, directive)
    b = _body_without_scale_banner(curr, directive)
    if a == b:
        return 0.0
    return 1.0 - difflib.SequenceMatcher(None, a, b).ratio()


def compose_style_first_prompt(prompt: str, scale_prof: dict[str, Any]) -> str:
    """Style directive first, user brief in the middle, redlines last."""
    clean_p = strip_redline_tags_from_generation_text(prompt or "")
    directive = str(scale_prof.get("prompt_directive") or "").strip()
    body = _body_without_scale_banner(clean_p, directive)
    tail = _constraint_tail(scale_prof)
    parts = [p for p in (directive, body, tail) if p]
    # Drop exact duplicates while keeping order.
    ordered: list[str] = []
    for part in parts:
        if part not in ordered:
            ordered.append(part)
    return " | ".join(ordered)


def get_converge_scale_profile(
    scale: str = "medium",
    recompose_dir: str = "",
    *,
    goal: str = "",
    ref_analysis: str = "",
    ref_image: str = "",
    module: str = "",
) -> dict[str, Any]:
    s = (scale or "medium").strip().lower()
    if s not in CONVERGE_SCALE_PROFILES:
        s = "medium"
    prof = dict(CONVERGE_SCALE_PROFILES[s])
    prof["dim_weights"] = dict(CONVERGE_SCALE_PROFILES[s]["dim_weights"])
    _, _, case_redlines = _infer_case_style_and_subject(
        goal=goal, ref_analysis=ref_analysis, ref_image=ref_image, module=module
    )
    merged_limits = list(CONVERGE_SCALE_PROFILES[s].get("forbidden_changes", []))
    if s == "low" and case_redlines:
        merged_limits = _merge_low_forbidden(merged_limits, case_redlines)
    prof["forbidden_changes"] = merged_limits
    prof["prompt_directive"] = build_dynamic_prompt_directive(
        s,
        goal=goal,
        ref_analysis=ref_analysis,
        ref_image=ref_image,
        module=module,
        recompose_dir=recompose_dir,
    )
    if recompose_dir:
        prof["recompose_dir"] = recompose_dir
    return prof


