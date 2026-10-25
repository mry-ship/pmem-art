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
        "min_rounds_before_stop": 1,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.15,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.25,
            "texture_detail": 0.25,
            "spec_style": 0.15,
        },
        # Retention: one pose/viewpoint lock + medium/identity. Do NOT stack "垫图一致性高" or coordinate DNA.
        "retention_set": ("viewpoint_or_pose", "style_medium", "identity"),
        "next_fix_budget": "conservative (~15% prompt delta, <=20% vs first)",
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
        "prompt_directive": "原图画风优先：锁视角与姿态，仅微修局部质感",
    },
    "medium": {
        "scale": "medium",
        "label": "中强度 · 补足加小优化动态达标闭环 (Balance & Polish Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        "min_rounds_before_stop": 1,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.15,
            "lighting_color": 0.30,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.20,
            "spec_style": 0.15,
        },
        # Keep medium + identity + camera frame; polish light/air/material. No coordinate DNA dump.
        "retention_set": ("viewpoint_frame", "style_medium", "identity"),
        "next_fix_budget": "moderate (~35% prompt delta, 25%–45%; cumulative <=60% vs first)",
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
        "min_round_leap": 0.15,
        "prompt_delta_baseline": "previous",
        # Stub only — NOT the live contract. get_converge_scale_profile always overwrites
        # via build_dynamic_prompt_directive (painterly may inject SSS; UI/pixel/flat skip it).
        "prompt_directive": "保画风与主体，柔化光影层次",
    },
    "high": {
        "scale": "high",
        "label": "高强度 · 大胆重构光影与张力动态达标闭环 (Showcase Overhaul Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        # Prevent 1-round "locked DNA photocopy" stop — drama needs at least one refine pass.
        "min_rounds_before_stop": 2,
        "target_score_threshold": 9.6,
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
        "next_fix_budget": "bold_overhaul (~65% prompt delta, 50%–80% / <=70% vs previous; cumulative <=85% vs first)",
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
        "min_round_leap": 0.20,
        "prompt_delta_baseline": "previous",
        # Fallback only — runtime rebuilds to V4-short skeleton (no 锁死/DNA/垫图一致性 tokens).
        "prompt_directive": "保媒介与身份，提升光影张力",
    },
    "recompose": {
        "scale": "recompose",
        "label": "定向改构图模式 · 按用户指定新构图动态达标闭环 (Directed Re-Composition Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 8,
        "min_rounds_before_stop": 2,
        "target_score_threshold": 9.6,
        "dim_weights": {
            "composition": 0.30,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.15,
            "spec_style": 0.15,
        },
        # Inherit brush/palette/identity; camera target = --recompose-dir, NOT the ref overhead/pose.
        "retention_set": ("style_medium", "identity", "recompose_dir_target"),
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
        "min_round_leap": 0.20,
        "prompt_directive": "保画风色板，按指令重构机位",
    },
}

# Optimal-direction overlays must ADD the scale's job — never a second lock.
# Keep free of affirmative lock tokens so preflight grep stays clean.
SCALE_BEST_DIRECTION_HINTS: dict[str, str] = {
    "low": "最优方向：微质感（瓦当/纸齿/发丝），≤40字",
    "medium": "最优方向：光影·空气透视·介质三条",
    "high": "最优方向：体积光/冷暖碰撞/轮廓光",
    "recompose": "最优方向：只写目标机位与布局",
    "recompose_bold": "最优方向：画幅比+剪影一句，风格叙事大跳",
}

# Affirmative lock phrases that must NOT appear in high/recompose/bold task text.
# Negation wrappers (勿/禁止/不要…) are exempt via find_affirmative_lock_hits().
AFFIRMATIVE_LOCK_PATTERNS: tuple[str, ...] = (
    r"严格保留(?:原构图)?\s*DNA",
    r"垫图一致性高",
    r"构图[：:]\s*锁死",
    r"严格锁死",
    r"核验DNA",
    r"保持坐姿DNA",
    r"保持天井DNA",
    r"保持胸像DNA",
    r"原构图\s*DNA",
)


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
    """V4-short skeletons: low=one pose lock; medium=light polish; high=drama; recompose=target camera."""
    s = (scale or "medium").strip().lower()
    style_head, has_char, _ = _infer_case_style_and_subject(
        goal=goal, ref_analysis=ref_analysis, ref_image=ref_image, module=module
    )
    if s == "low":
        body = "锁视角与姿态，仅微修局部质感" if has_char else "锁视角与布局，仅微修局部质感"
        return f"{style_head}：{body}"
    if s == "medium":
        # Match historical SSS gating: only style_head + goal (not ref_analysis asides like「略有水彩」).
        blob = f"{style_head} {goal}"
        mod_l = (module or "").strip().lower()
        no_sss = (
            mod_l == "ui"
            or mod_l.startswith("ui.")
            or mod_l.startswith("icon.")
            or "pixel" in mod_l
            or any(k in blob.lower() for k in ("像素", "pixel", "ui kit", "九宫格", "hud"))
        )
        if no_sss:
            return f"{style_head}：保画风与主体，加强色块边界与材质可读性"
        if any(k in blob for k in ("速写", "粉彩", "水彩", "浮世绘", "水墨", "线稿", "pastel", "sketch", "ukiyoe")):
            return f"{style_head}：保画风与主体，柔化光影与留白层次"
        # Painterly / film (incl. canyon thick-paint): short SSS cue; UI/pixel skipped above.
        return f"{style_head}：保画风与主体，柔化光影与次表面散射"
    if s == "high":
        # Short V4 skeleton — ban-lists live in skill docs / preflight, not in the gen string.
        return f"{style_head}：保媒介与身份，提升光影张力"
    target = (recompose_dir or "").strip() or "指定新机位与景别"
    return f"{style_head}：保画风色板，按「{target}」重构机位"


def build_best_direction_hint(scale: str = "medium", *, recompose_bold: bool = False) -> str:
    """Per-scale optimal-direction overlay. Never a second lock."""
    s = (scale or "medium").strip().lower()
    if recompose_bold or s in ("bold", "recompose_bold"):
        return SCALE_BEST_DIRECTION_HINTS["recompose_bold"]
    return SCALE_BEST_DIRECTION_HINTS.get(s, SCALE_BEST_DIRECTION_HINTS["medium"])


_NEGATION_BEFORE_LOCK = re.compile(
    r"(?:勿写|勿复读|勿重申|勿|禁止|不要|并非|未|无|别)[\s\S]{0,12}$"
)


def find_affirmative_lock_hits(text: str) -> list[str]:
    """Return affirmative lock phrases (strict DNA / pad-consistency / 锁死). Negations exempt."""
    raw = str(text or "")
    if not raw.strip():
        return []
    hits: list[str] = []
    for pat in AFFIRMATIVE_LOCK_PATTERNS:
        for m in re.finditer(pat, raw, flags=re.IGNORECASE):
            prefix = raw[max(0, m.start() - 12) : m.start()]
            if _NEGATION_BEFORE_LOCK.search(prefix):
                continue
            hits.append(m.group(0))
    return hits


def check_scale_task_text(
    *,
    scale: str,
    goal: str = "",
    prompt: str = "",
    best_direction: str = "",
    recompose_dir: str = "",
    recompose_bold: bool = False,
) -> dict[str, Any]:
    """Preflight (no image): affirmative locks, recompose camera wording, min_rounds."""
    s = (scale or "medium").strip().lower()
    if recompose_bold:
        s = "recompose"
    prof = get_converge_scale_profile(
        s,
        recompose_dir=recompose_dir,
        goal=goal,
    )
    blob = "\n".join(
        [
            str(goal or ""),
            str(prompt or ""),
            str(best_direction or ""),
            str(recompose_dir or ""),
            str(prof.get("prompt_directive") or ""),
            str(prof.get("best_direction_hint") or ""),
        ]
    )
    issues: list[str] = []
    lock_hits = find_affirmative_lock_hits(blob)
    if s in ("high", "recompose") or recompose_bold:
        if lock_hits:
            issues.append(f"肯定锁命中: {sorted(set(lock_hits))}")
    if s == "recompose":
        g = str(goal or "") + " " + str(recompose_dir or "")
        # Scene + portrait camera lexicon (not night-city only).
        new_cam = (
            "阳台", "花格", "过肩", "仰视", "侧机位", "低机位", "平视", "运河", "天台",
            "肩线", "回眸", "半身", "特写", "俯视", "仰拍", "露台", "回廊",
        )
        old_cam = ("高空俯瞰", "左下飞檐")
        if not any(t in g for t in new_cam):
            issues.append("recompose 未含新机位词（阳台/花格/过肩/仰视/肩线/…）")
        if any(t in g for t in old_cam):
            issues.append("recompose 仍含原俯瞰句（高空俯瞰/左下飞檐）")
    min_r = int(prof.get("min_rounds_before_stop") or 1)
    if s in ("high", "recompose") and min_r < 2:
        issues.append(f"{s} min_rounds_before_stop={min_r} < 2")
    # Built-in directive/hint themselves must be clean for high/recompose.
    for label, piece in (
        ("directive", prof.get("prompt_directive")),
        ("best_direction_hint", prof.get("best_direction_hint")),
    ):
        if s in ("high", "recompose") or recompose_bold:
            h = find_affirmative_lock_hits(str(piece or ""))
            if h:
                issues.append(f"内置{label}含肯定锁: {h}")
    return {
        "ok": not issues,
        "scale": s,
        "min_rounds_before_stop": min_r,
        "lock_hits": lock_hits,
        "issues": issues,
        "prompt_directive": prof.get("prompt_directive"),
        "best_direction_hint": prof.get("best_direction_hint"),
    }


def _recompose_change_evidence(text: str, recompose_dir: str = "") -> bool:
    """True if judge text / prompt shows camera or layout actually moved toward recompose-dir."""
    blob = str(text or "")
    if not blob.strip():
        return False
    low = blob.lower()
    cues = (
        "机位", "视角", "仰视", "俯视", "侧视", "平视", "低机位", "高机位",
        "改为", "换机位", "重构机位", "重排", "新构图", "viewpoint", "camera",
        "low angle", "high angle", "bird", "worm",
    )
    if any(c.lower() in low for c in cues):
        return True
    direction = str(recompose_dir or "").strip()
    if not direction:
        return False
    # Distinctive tokens from --recompose-dir (len>=2) appearing in the blob.
    parts = re.split(r"[\s，,。；;、/|]+", direction)
    hits = 0
    for p in parts:
        tok = p.strip()
        if len(tok) < 2:
            continue
        if tok.lower() in low or tok in blob:
            hits += 1
    return hits >= 2


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


# Clauses that must never ride into a composed generation prompt (retention_set enforcement).
_OVERREACH_LOCK_CLAUSES: tuple[re.Pattern[str], ...] = (
    re.compile(r"严格保留(?:原构图)?\s*DNA[^；;|，,\n]*", re.I),
    re.compile(r"参考垫图一致性高[^；;|，,\n]*", re.I),
    re.compile(r"垫图一致性高[^；;|，,\n]*", re.I),
    re.compile(r"构图[：:]\s*锁死[^；;|，,\n]*", re.I),
    re.compile(r"核验DNA[：:][^；;|，,\n]*", re.I),
    re.compile(r"保持(?:坐姿|天井|胸像)DNA[^；;|，,\n]*", re.I),
    re.compile(r"原构图\s*DNA[^；;|，,\n]*", re.I),
)


def strip_affirmative_locks_from_prompt(text: str, *, scale: str = "") -> str:
    """Strip overreach DNA / pad-consistency / 构图锁死 clauses. retention_set actually bites here."""
    raw = str(text or "")
    if not raw.strip():
        return ""
    cleaned = raw
    for pat in _OVERREACH_LOCK_CLAUSES:
        cleaned = pat.sub(" ", cleaned)
    # high / recompose: also drop leftover「严格锁死…」coordinate dumps
    s = (scale or "").strip().lower()
    if s in ("high", "recompose") or s.endswith("_best") or "bold" in s:
        cleaned = re.sub(r"严格锁死[^；;|，,\n]*", " ", cleaned)
    cleaned = re.sub(r"[|；;]{2,}", "|", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    return cleaned.strip(" |；;，,")


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
    scale = str(scale_prof.get("scale") or "")
    clean_p = strip_redline_tags_from_generation_text(prompt or "")
    clean_p = strip_affirmative_locks_from_prompt(clean_p, scale=scale)
    directive = str(scale_prof.get("prompt_directive") or "").strip()
    directive = strip_affirmative_locks_from_prompt(directive, scale=scale)
    body = _body_without_scale_banner(clean_p, directive)
    body = strip_affirmative_locks_from_prompt(body, scale=scale)
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
    prof["best_direction_hint"] = build_best_direction_hint(s)
    prof["min_rounds_before_stop"] = int(
        CONVERGE_SCALE_PROFILES[s].get("min_rounds_before_stop") or 1
    )
    if recompose_dir:
        prof["recompose_dir"] = recompose_dir
    return prof


