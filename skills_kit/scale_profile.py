"""Scale profiles and case-style inference. Moved out of prompt_scale so judge code can use it
without importing the prompt-composition layer.
"""
from __future__ import annotations

from typing import Any

CONVERGE_SCALE_PROFILES: dict[str, dict[str, Any]] = {
    "low": {
        "scale": "low",
        "label": "低强度 · 保守修瑕动态达标闭环 (Defect-Fix Dynamic Threshold >=9.5)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
        "min_rounds_before_stop": 1,
        "target_score_threshold": 9.5,
        "dim_weights": {
            "composition": 0.15,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.25,
            "texture_detail": 0.25,
            "spec_style": 0.15,
        },
        # Retention: one pose/viewpoint lock + medium/identity. Do NOT stack "垫图一致性高" or coordinate DNA.
        "retention_set": ("viewpoint_or_pose", "style_medium", "identity"),
        "next_fix_budget": "每轮都垫最初的参考图，只在提示词上补还没过的那一处（提示词改动仍 ≤20%）",
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
        # Soft leap: strong ref-image runs often move +0.10~0.20; 0.12 was noisy.
        "min_round_leap": 0.10,
        "prompt_delta_baseline": "first",
        "prompt_directive": (
            "原图画风优先：锁视角与姿态落点（手和脚的触点跟参考像素），仅微修局部质感"
        ),
    },
    "medium": {
        "scale": "medium",
        "label": "中强度 · 小优化（锁机位）动态达标闭环 (Balance & Polish Dynamic Threshold >=9.5)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
        "min_rounds_before_stop": 1,
        "target_score_threshold": 9.5,
        "dim_weights": {
            # Align v2 mid feel: lighting ≈25%; still camera-locked polish.
            "composition": 0.20,
            "lighting_color": 0.25,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.20,
            "spec_style": 0.15,
        },
        # Keep viewpoint + medium + identity; allow small pose / local layout / lighting polish.
        "retention_set": ("viewpoint_frame", "style_medium", "identity"),
        "next_fix_budget": "每轮都垫最初的参考图，只在提示词上补还没过的那一处（提示词改动仍 ≤40%）",
        "max_prompt_delta_ratio": 0.40,
        "allow_recompose": False,
        "allow_viewpoint_change": False,
        "allow_action_pose_change": True,
        "allow_element_count_change": False,
        "allow_layout_change": True,
        "allow_lighting_overhaul": True,
        "forbidden_changes": [
            "viewpoint_angle (不改机位与镜头视角)",
            "element_count (不增删主体元素清单)",
            "no_full_recompose (不做整体 recompose / 换景别故事)",
            "style_medium (保持原图画风笔触与色板)",
            "identity_lock (保持原图性别、物种、年龄段与核心外观)",
        ],
        "min_round_leap": 0.15,
        "prompt_delta_baseline": "previous",
        # Stub only — NOT the live contract. get_converge_scale_profile always overwrites
        # via build_dynamic_prompt_directive (painterly may inject SSS; UI/pixel/flat skip it).
        "prompt_directive": "保画风与机位，小幅姿态/局部布局与光影优化",
    },
    "high": {
        "scale": "high",
        "label": "高强度 · 大胆跃升+可叙事动态达标闭环 (Showcase Overhaul Dynamic Threshold >=9.5)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
        # Prevent 1-round "locked DNA photocopy" stop — drama needs at least one refine pass.
        "min_rounds_before_stop": 2,
        "target_score_threshold": 9.5,
        "dim_weights": {
            # Favor lighting/drama over structural photocopy rewards.
            "composition": 0.15,
            "lighting_color": 0.30,
            "perspective_anatomy": 0.15,
            "texture_detail": 0.20,
            "spec_style": 0.20,
        },
        # Only medium gene + identity — NOT original camera coordinates / 垫图一致性.
        "retention_set": ("style_medium", "identity"),
        "next_fix_budget": "每轮都垫最初的参考图；第 1 轮可以拉开光影，之后只在提示词上补还没过的那一处（提示词改动仍 ≤80%）",
        "max_prompt_delta_ratio": 0.80,
        "allow_recompose": True,
        "allow_viewpoint_change": True,
        "allow_action_pose_change": True,
        "allow_element_count_change": True,
        "allow_layout_change": True,
        "allow_lighting_overhaul": True,
        "forbidden_changes": [
            "style_medium (保持原图核心艺术媒介与画风基因)",
            "identity_lock (保持原图性别、物种、年龄段与核心外观)",
            # Allow in-style narrative accents; do not swap subject identity.
            "no_identity_swap (可加风格内叙事点缀，不换主体身份)",
        ],
        "min_round_leap": 0.20,
        "prompt_delta_baseline": "previous",
        # Fallback only — runtime rebuilds to V4-short skeleton (no 锁死/DNA/垫图一致性 tokens).
        "prompt_directive": "保媒介与身份，提升光影张力；可加风格内叙事点缀",
    },
    "recompose": {
        "scale": "recompose",
        "label": "定向改构图模式 · 按用户指定新构图动态达标闭环 (Directed Re-Composition Dynamic Threshold >=9.5)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
        "min_rounds_before_stop": 2,
        "target_score_threshold": 9.5,
        "dim_weights": {
            "composition": 0.30,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.15,
            "spec_style": 0.15,
        },
        # Inherit brush/palette/identity; camera target = --recompose-dir, NOT the ref overhead/pose.
        "retention_set": ("style_medium", "identity", "recompose_dir_target"),
        "next_fix_budget": "每轮都垫最初的参考图；第 1 轮落到指定机位，之后只在提示词上补还没过的那一处（提示词改动仍 ≤85%）",
        "max_prompt_delta_ratio": 0.85,
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
        "min_round_leap": 0.20,
        "prompt_directive": "保画风色板，按指令重构机位",
    },
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
    if any(k in b for k in ("植物志", "水彩植物", "botanical")):
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
    has_ref = bool(str(ref_image or "").strip())
    mod = str(module or "")
    # 无垫图时禁止写「原图画风优先」：模型会落到写实默认（食物=棚拍）。
    if has_ref:
        style_head = "原图画风优先"
    elif mod.startswith("merge.") or "merge" in blob or "合成梯" in blob:
        style_head = "品类默认画风优先"
    else:
        style_head = "题材画风优先"
    if has_ref:
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
    else:
        case_redlines = [
            "style_surface (跟提示词品类默认画风)",
        ]
    return style_head, has_char, case_redlines


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


def get_converge_scale_profile(
    scale: str = "medium",
    recompose_dir: str = "",
    *,
    goal: str = "",
    ref_analysis: str = "",
    ref_image: str = "",
    module: str = "",
    medium_family: str = "",
    contract: str = "",
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
    # 无垫图：去掉角色改图「保原图画风 / 性别物种」约束，避免 jam/merge 整表落到写实默认。
    if not str(ref_image or "").strip():
        cleaned_limits: list[str] = []
        for item in merged_limits:
            text = str(item)
            if "保持原图画风" in text or "原图核心艺术媒介" in text:
                continue
            if "性别、物种、年龄段" in text:
                continue
            cleaned_limits.append(item)
        if not any("style_surface" in str(x) or "品类默认画风" in str(x) for x in cleaned_limits):
            cleaned_limits.append("style_surface (跟提示词品类默认画风)")
        merged_limits = cleaned_limits
    prof["forbidden_changes"] = merged_limits
    from .medium_family import apply_family_to_profile, infer_medium_family

    style_head, _, _ = _infer_case_style_and_subject(
        goal=goal, ref_analysis=ref_analysis, ref_image=ref_image, module=module
    )
    family = (medium_family or "").strip().lower()
    if not family:
        # 旁注里的「略有水彩 / 远景水墨」不改这一家。先看题材和案例画风。
        family = infer_medium_family(goal, module, style_head)
        if family == "generic":
            ref_text = ref_analysis if isinstance(ref_analysis, str) else ""
            family = infer_medium_family(goal, ref_text, ref_image, module, style_head)
    apply_family_to_profile(
        prof,
        family=family,
        recompose_dir=recompose_dir,
        style_head=style_head,
        contract=(contract or "").strip().lower(),
    )
    mod_l = (module or "").strip().lower()
    if s == "medium" and mod_l.startswith("prop.") and "pixel" not in mod_l:
        if "表面那一句不动" not in str(prof.get("prompt_directive") or ""):
            prof["prompt_directive"] = (
                str(prof.get("prompt_directive") or "").rstrip("。")
                + "，表面那一句不动，只修没过的那一格"
            )
    prof["min_rounds_before_stop"] = int(
        CONVERGE_SCALE_PROFILES[s].get("min_rounds_before_stop") or 1
    )
    if recompose_dir:
        prof["recompose_dir"] = recompose_dir
    prof["goal"] = goal or ""
    prof["module"] = module or ""
    prof["ref_image"] = ref_image or ""
    if isinstance(ref_analysis, dict):
        prof["ref_analysis"] = " ".join(str(v or "") for v in ref_analysis.values())
    else:
        prof["ref_analysis"] = str(ref_analysis or "")
    return prof
