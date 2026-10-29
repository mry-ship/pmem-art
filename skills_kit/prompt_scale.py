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
DEFAULT_MAX_ROUNDS = 4
FAST_SOFT_THRESHOLD = 9.0  # fast-track: prefer fewer regens when score>=9.0 & delta small; final accept still >=9.6 unless draft
# Physical image gate: solid-gray probes sit ~2.5–2.9; real art JPEGs are typically ≥6.
MIN_IMAGE_BYTE_ENTROPY = 3.2
MIN_IMAGE_EDGE_PX = 64

CONVERGE_SCALE_PROFILES: dict[str, dict[str, Any]] = {
    "low": {
        "scale": "low",
        "label": "低强度 · 保守修瑕动态达标闭环 (Defect-Fix Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
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
        "prompt_directive": "原图画风优先：锁视角与姿态，仅微修局部质感",
    },
    "medium": {
        "scale": "medium",
        "label": "中强度 · 小优化（锁机位）动态达标闭环 (Balance & Polish Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
        "min_rounds_before_stop": 1,
        "target_score_threshold": 9.6,
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
        "label": "高强度 · 大胆跃升+可叙事动态达标闭环 (Showcase Overhaul Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
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
        "label": "定向改构图模式 · 按用户指定新构图动态达标闭环 (Directed Re-Composition Dynamic Threshold >=9.6)",
        "stop_policy": "dynamic_threshold",
        "max_rounds": 4,
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

# Optimal-direction overlays must ADD the scale's job — never a second lock.
# Keep free of affirmative lock tokens so preflight grep stays clean.
SCALE_BEST_DIRECTION_HINTS: dict[str, str] = {
    "low": "最优方向：微质感（瓦当/纸齿/发丝），≤40字",
    "medium": "最优方向：光影·空气·介质；可小幅姿态/局部布局",
    "high": "最优方向：体积光/冷暖碰撞/轮廓光/叙事点缀",
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


def classify_subject(
    *,
    goal: str = "",
    ref_analysis: Any = "",
    ref_image: str = "",
    module: str = "",
) -> str:
    """ui | humanoid | creature | both | mechanical | scene | generic | unknown.

    Latin cues match whole tokens. Unrecognized briefs stay ``unknown``.
    Chinese phrases are for reading the lexicon; the sentence written into the
    prompt is the English twin (see ``build_r1_structure_floor``).
    """
    from .subject_lexicon import classify_subject_kind

    return classify_subject_kind(
        goal=goal, ref_analysis=ref_analysis, ref_image=ref_image, module=module
    )


def build_r1_structure_floor(
    *,
    goal: str = "",
    ref_analysis: Any = "",
    ref_image: str = "",
    module: str = "",
    lang: str = "en",
) -> str:
    """Structure sentence for the prompt (English) or the chat echo (``lang='zh'``).

    Unknown UI briefs return "". Clone UI shell briefs (ui.* + empty-center markers) inject ui_shell floor.
    """
    from .subject_lexicon import (
        clone_style_lock_new_subject_task,
        floor_sentence,
        ui_shell_clone_task,
    )

    if ui_shell_clone_task(goal=goal, ref_analysis=ref_analysis, module=module):
        return floor_sentence("ui_shell", lang)
    if clone_style_lock_new_subject_task(
        goal=goal,
        ref_analysis=ref_analysis,
        module=module,
        ref_image=ref_image,
    ):
        return floor_sentence("clone_subject", lang)
    kind = classify_subject(
        goal=goal, ref_analysis=ref_analysis, ref_image=ref_image, module=module
    )
    if kind in ("ui", "unknown"):
        return ""
    return floor_sentence(kind, lang)


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
        # v2 mid feel: lock camera; allow small pose / local layout + lighting polish.
        if no_sss:
            return f"{style_head}：保画风与机位，小幅姿态/局部布局；加强色块边界与材质可读性"
        if mod_l.startswith("prop."):
            return f"{style_head}：保画风与机位，表面那一句不动，只修没过的那一格"
        if any(k in blob for k in ("速写", "粉彩", "水彩", "浮世绘", "水墨", "线稿", "pastel", "sketch", "ukiyoe")):
            return f"{style_head}：保画风与机位，小幅姿态/局部布局；柔化光影与留白层次"
        # Painterly / film (incl. canyon thick-paint): short SSS cue; UI/pixel skipped above.
        return f"{style_head}：保画风与机位，小幅姿态/局部布局；柔化光影与次表面散射"
    if s == "high":
        # Short V4 skeleton — ban-lists live in skill docs / preflight, not in the gen string.
        return f"{style_head}：保媒介与身份，提升光影张力；可加风格内叙事点缀"
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
    if s == "recompose" and not recompose_bold:
        g = str(goal or "") + " " + str(recompose_dir or "")
        # Scene + portrait camera lexicon (not night-city only).
        new_cam = (
            "阳台", "花格", "过肩", "仰视", "侧机位", "低机位", "平视", "运河", "天台",
            "肩线", "回眸", "半身", "特写", "俯视", "仰拍", "露台", "回廊",
            "乌篷", "拱桥", "石桥", "温室", "藤椅",
        )
        old_cam = ("高空俯瞰", "左下飞檐")
        if not any(t in g for t in new_cam):
            issues.append("recompose 未含新机位词（阳台/花格/过肩/仰视/肩线/…）")
        if any(t in g for t in old_cam):
            issues.append("recompose 仍含原俯瞰句（高空俯瞰/左下飞檐）")
    if recompose_bold:
        # Bold = style bible + silhouette only; must NOT require/reuse recompose camera dir.
        g = str(goal or "") + " " + str(prompt or "")
        style_cues = ("风格", "style", "剪影", "赛博", "波普", "浮世绘", "动漫", "跳变", "圣经")
        if not any(t.lower() in g.lower() for t in style_cues):
            issues.append("recompose_bold 未含风格/剪影跳变词")
        if str(recompose_dir or "").strip():
            issues.append("recompose_bold 不应携带 recompose_dir 机位（与 recompose 拆开）")
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


_RECOMPOSE_NEGATIVE = (
    "没换机位",
    "未换机位",
    "机位没换",
    "不改机位",
    "仍是原机位",
    "仍偏俯看",
    "did not recompose",
    "still the original",
    "still high-roof",
    "camera still",
    "warrior still a large",
    "four-round recompose miss",
)


def _recompose_change_evidence(text: str, recompose_dir: str = "") -> bool:
    """True if the look-at-image writeup shows the plate moved toward recompose-dir.

    Prompt text does not count: 「重构机位」 is an instruction, not proof.
    Explicit 'did not recompose / 没换机位' always returns False.
    """
    blob = str(text or "")
    if not blob.strip():
        return False
    low = blob.lower()
    if any(n.lower() in low for n in _RECOMPOSE_NEGATIVE):
        return False
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


def _apply_prompt_language_and_stubs(
    text: str,
    scale_prof: dict[str, Any],
    stub_notes: list[str] | None,
) -> str:
    """Known Chinese clauses become English. Toy-medium words drop unless the brief declared them."""
    from .subject_lexicon import strip_foreign_medium_stubs, to_prompt_english

    english = to_prompt_english(text)
    cleaned, removed = strip_foreign_medium_stubs(
        english,
        goal=str(scale_prof.get("goal") or ""),
        module=str(scale_prof.get("module") or ""),
        ref_analysis=scale_prof.get("ref_analysis") or "",
    )
    if stub_notes is not None and removed:
        stub_notes.extend(removed)
    return cleaned


def compose_continuation_prompt(
    fix: str,
    scale_prof: dict[str, Any],
    *,
    stub_notes: list[str] | None = None,
) -> str:
    """Round 2+: the pad is the previous plate. Name one repair; do not restate the scene."""
    scale = str(scale_prof.get("scale") or "")
    directive = strip_affirmative_locks_from_prompt(
        str(scale_prof.get("prompt_directive") or "").strip(),
        scale=scale,
    )
    one = strip_affirmative_locks_from_prompt(
        strip_redline_tags_from_generation_text(fix or "").strip(),
        scale=scale,
    )
    if not one:
        one = "只补这一张里还没到位的那一处"
    direction = str(scale_prof.get("recompose_dir") or "").strip()
    keep_camera = ""
    if scale == "recompose" and direction:
        keep_camera = f"机位保持指定方向：{direction}。"
    edit = f"{keep_camera}垫图是目前分数最高的那张成图。只改这一处：{one}。没点名的地方保持垫图。"
    ordered: list[str] = []
    for part in (directive, edit):
        if part and part not in ordered:
            ordered.append(part)
    return _apply_prompt_language_and_stubs(" | ".join(ordered), scale_prof, stub_notes)


def compose_style_first_prompt(
    prompt: str,
    scale_prof: dict[str, Any],
    *,
    stub_notes: list[str] | None = None,
) -> str:
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
    return _apply_prompt_language_and_stubs(" | ".join(ordered), scale_prof, stub_notes)


_DIM_WEIGHT_ZH: dict[str, str] = {
    "composition": "构图",
    "lighting_color": "光影色彩",
    "perspective_anatomy": "透视与解剖",
    "texture_detail": "质感",
    "spec_style": "规格与风格",
    "flawlessness": "无瑕疵",
}

_SCALE_LABEL_ZH: dict[str, str] = {
    "low": "低强度 · 贴原修瑕",
    "medium": "中强度 · 小优化（锁机位）",
    "high": "高强度 · 大胆跃升+可叙事",
    "recompose": "定向改构图",
}

_RETENTION_ZH: dict[str, str] = {
    "viewpoint_or_pose": "视角/姿态",
    "viewpoint_frame": "机位画幅",
    "style_medium": "画风媒介与色板",
    "identity": "身份外观",
    "recompose_dir_target": "用户指定的新机位目标",
}

# Artist-facing lock intensity % per 5D axis (NOT judge score weights).
# 100% = 完全锁死不可动；0% = 本档可大胆改。画家可说「光影锁定降到 40%」。
SCALE_DIM_LOCK_LEVELS: dict[str, dict[str, tuple[int, str]]] = {
    "low": {
        "composition": (95, "几乎不改机位、景别与布局"),
        "lighting_color": (75, "不大翻主光；局部明暗可微修"),
        "perspective_anatomy": (80, "可修硬伤，不改姿态动作"),
        "texture_detail": (25, "本档主战场：边缘、材质、小瑕疵"),
        "spec_style": (95, "画风笔触、色板与身份几乎不动"),
        "flawlessness": (90, "脏点必须修；这一维由看图的人打，不靠空话"),
    },
    "medium": {
        "composition": (85, "锁机位；允许局部布局微调，禁止整体 recompose"),
        "lighting_color": (30, "本档主战场：光影层次、空气感、介质"),
        "perspective_anatomy": (55, "允许小幅姿态；可修局部结构"),
        "texture_detail": (35, "材质与边缘可抛光"),
        "spec_style": (90, "画风与身份几乎不动"),
        "flawlessness": (90, "脏点必须修；这一维由看图的人打，不靠空话"),
    },
    "high": {
        "composition": (30, "允许机位/布局/元素数为张力与叙事服务"),
        "lighting_color": (20, "只抬这一家已经有的光；体积光只在厚涂"),
        "perspective_anatomy": (40, "姿态可动，仍保身份可读"),
        "texture_detail": (35, "材质可跟光影一起升级"),
        "spec_style": (70, "锁媒介基因；no_identity_swap 可加风格内点缀"),
        "flawlessness": (80, "脏点必须修；这一维由看图的人打，不靠空话"),
    },
    "recompose": {
        "composition": (15, "按 --recompose-dir 重构机位/布局（主战场）"),
        "lighting_color": (40, "可随新机位重铺光影"),
        "perspective_anatomy": (35, "透视随新机位重建"),
        "texture_detail": (40, "材质跟新构图走"),
        "spec_style": (75, "画风色板与身份仍偏锁"),
        "flawlessness": (80, "脏点必须修；这一维由看图的人打，不靠空话"),
    },
}


def format_dim_weights_zh(weights: dict[str, Any] | None) -> str:
    """Judge score weights, e.g. 构图15% · 光影色彩20% · … (internal; not artist lock levels)."""
    if not isinstance(weights, dict) or not weights:
        return "（无权重）"
    parts: list[str] = []
    for key, label in _DIM_WEIGHT_ZH.items():
        if key not in weights:
            continue
        try:
            pct = int(round(float(weights[key]) * 100))
        except (TypeError, ValueError):
            continue
        parts.append(f"{label}{pct}%")
    if not parts:
        for k, v in weights.items():
            try:
                pct = int(round(float(v) * 100))
            except (TypeError, ValueError):
                continue
            parts.append(f"{_DIM_WEIGHT_ZH.get(str(k), str(k))}{pct}%")
    return " · ".join(parts) if parts else "（无权重）"


_DIM_ALIAS_TO_KEY: dict[str, str] = {
    "构图": "composition",
    "composition": "composition",
    "光影": "lighting_color",
    "光影色彩": "lighting_color",
    "色彩": "lighting_color",
    "lighting": "lighting_color",
    "lighting_color": "lighting_color",
    "透视": "perspective_anatomy",
    "解剖": "perspective_anatomy",
    "透视与解剖": "perspective_anatomy",
    "透视解剖": "perspective_anatomy",
    "perspective": "perspective_anatomy",
    "perspective_anatomy": "perspective_anatomy",
    "质感": "texture_detail",
    "材质": "texture_detail",
    "细节": "texture_detail",
    "texture": "texture_detail",
    "texture_detail": "texture_detail",
    "规格": "spec_style",
    "风格": "spec_style",
    "规格与风格": "spec_style",
    "规格风格": "spec_style",
    "style": "spec_style",
    "spec_style": "spec_style",
    "无瑕疵": "flawlessness",
    "无暇": "flawlessness",
    "flawlessness": "flawlessness",
}

LOCK_RELAX_STEP = 20  # 「松一点」默认下调锁定%
LOCK_TIGHTEN_STEP = 15  # 「紧一点」默认上调


def get_base_dim_lock_pct(scale: str, dim_key: str) -> int:
    s = (scale or "medium").strip().lower()
    if s not in SCALE_DIM_LOCK_LEVELS:
        s = "medium"
    pct, _ = SCALE_DIM_LOCK_LEVELS[s].get(dim_key, (50, ""))
    return int(pct)


def resolve_dim_lock_levels(
    scale: str = "medium",
    overrides: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Per-dim rows with base vs effective lock %.
    overrides: {composition: 70, ...} absolute targets after artist fine-tune.
    """
    s = (scale or "medium").strip().lower()
    if s not in SCALE_DIM_LOCK_LEVELS:
        s = "medium"
    ov: dict[str, int] = {}
    if isinstance(overrides, dict):
        for k, v in overrides.items():
            key = _DIM_ALIAS_TO_KEY.get(str(k).strip().lower()) or _DIM_ALIAS_TO_KEY.get(str(k).strip())
            if not key:
                key = str(k).strip()
            if key not in _DIM_WEIGHT_ZH:
                continue
            try:
                ov[key] = max(0, min(100, int(round(float(v)))))
            except (TypeError, ValueError):
                continue
    rows_out: list[dict[str, Any]] = []
    for key, label in _DIM_WEIGHT_ZH.items():
        base, note = SCALE_DIM_LOCK_LEVELS[s].get(key, (50, ""))
        base_i = int(base)
        eff = int(ov[key]) if key in ov else base_i
        changed = eff != base_i
        delta = eff - base_i
        if changed and delta < 0:
            note = f"{note}（画师放宽 {delta}%：{base_i}% → {eff}%）"
        elif changed and delta > 0:
            note = f"{note}（画师收紧 +{delta}%：{base_i}% → {eff}%）"
        rows_out.append(
            {
                "key": key,
                "label": label,
                "base": base_i,
                "effective": eff,
                "delta": delta,
                "changed": changed,
                "note": note,
            }
        )
    return rows_out


def parse_dim_lock_overrides(
    text: str,
    *,
    scale: str = "medium",
    current: dict[str, Any] | None = None,
) -> dict[str, int]:
    """
    Parse artist one-liners into absolute lock-% overrides.
    Examples: 「构图松一点」「光影锁定降到 40%」「构图=60」「透视再紧一点」
    """
    raw = str(text or "").strip()
    if not raw:
        return {}
    s = (scale or "medium").strip().lower()
    cur: dict[str, int] = {}
    if isinstance(current, dict):
        for k, v in current.items():
            key = _DIM_ALIAS_TO_KEY.get(str(k).strip()) or _DIM_ALIAS_TO_KEY.get(str(k).strip().lower()) or str(k)
            if key in _DIM_WEIGHT_ZH:
                try:
                    cur[key] = int(round(float(v)))
                except (TypeError, ValueError):
                    pass

    def _eff(key: str) -> int:
        if key in cur:
            return cur[key]
        return get_base_dim_lock_pct(s, key)

    found: dict[str, int] = {}
    # Explicit kv: 构图=60 / composition:70 / 光影锁定 40%
    for m in re.finditer(
        r"(构图|光影色彩|光影|透视与解剖|透视解剖|透视|解剖|质感|材质|规格与风格|规格风格|风格|规格|无瑕疵|"
        r"composition|lighting_color|perspective_anatomy|texture_detail|spec_style|flawlessness)"
        r"\s*(?:的?\s*锁定(?:程度)?\s*)?(?:[=:：]|降到|调到|改为|改到|到)\s*(\d{1,3})\s*%?",
        raw,
        flags=re.I,
    ):
        key = _DIM_ALIAS_TO_KEY.get(m.group(1)) or _DIM_ALIAS_TO_KEY.get(m.group(1).lower())
        if key:
            found[key] = max(0, min(100, int(m.group(2))))

    # Relative relax / tighten
    for m in re.finditer(
        r"(构图|光影色彩|光影|透视与解剖|透视解剖|透视|解剖|质感|材质|规格与风格|规格风格|风格|规格|无瑕疵)"
        r".{0,10}(再?松一点|松一些|放宽|松点儿|放松|再松)",
        raw,
    ):
        key = _DIM_ALIAS_TO_KEY.get(m.group(1))
        if key and key not in found:
            found[key] = max(0, _eff(key) - LOCK_RELAX_STEP)
    for m in re.finditer(
        r"(构图|光影色彩|光影|透视与解剖|透视解剖|透视|解剖|质感|材质|规格与风格|规格风格|风格|规格|无瑕疵)"
        r".{0,10}(再?紧一点|紧一些|收紧|再紧)",
        raw,
    ):
        key = _DIM_ALIAS_TO_KEY.get(m.group(1))
        if key and key not in found:
            found[key] = min(100, _eff(key) + LOCK_TIGHTEN_STEP)

    return found


def merge_dim_lock_overrides(
    scale: str,
    existing: dict[str, Any] | None,
    *texts: str,
) -> dict[str, int]:
    """Fold artist texts into absolute overrides (later text wins per dim)."""
    merged: dict[str, int] = {}
    if isinstance(existing, dict):
        for k, v in existing.items():
            key = _DIM_ALIAS_TO_KEY.get(str(k).strip()) or _DIM_ALIAS_TO_KEY.get(str(k).strip().lower()) or str(k)
            if key in _DIM_WEIGHT_ZH:
                try:
                    merged[key] = max(0, min(100, int(round(float(v)))))
                except (TypeError, ValueError):
                    pass
    for text in texts:
        parsed = parse_dim_lock_overrides(text, scale=scale, current=merged)
        merged.update(parsed)
    return merged


def _format_lock_delta_s(delta: int) -> str:
    return f"{delta}%" if delta < 0 else f"+{delta}%"


def _format_lock_pct_cell(row: dict[str, Any]) -> str:
    """Always show 有效%（默认X%，±Y%） so artists see every dial."""
    delta = int(row.get("delta") or 0)
    return (
        f"**{row['effective']}%**（默认{row['base']}%，**{_format_lock_delta_s(delta)}**）"
    )


def format_dim_lock_levels_zh(
    scale: str = "medium",
    overrides: dict[str, Any] | None = None,
) -> list[str]:
    """Markdown table: every dim shows effective%（默认base%，±delta%）."""
    lines = [
        "| 维度 | 锁定%（有效 · 默认 · 相对增减） | 含义 |",
        "| :--- | :---: | :--- |",
    ]
    for row in resolve_dim_lock_levels(scale, overrides):
        lines.append(f"| {row['label']} | {_format_lock_pct_cell(row)} | {row['note']} |")
    return lines


def format_dim_lock_summary_zh(
    scale: str = "medium",
    overrides: dict[str, Any] | None = None,
) -> str:
    """One-liner: every dim 构图75%(-20) / 光影75%(+0)."""
    parts: list[str] = []
    for row in resolve_dim_lock_levels(scale, overrides):
        d = int(row.get("delta") or 0)
        d_s = f"{d}" if d < 0 else f"+{d}"
        parts.append(f"{row['label']}{row['effective']}%({d_s})")
    return " · ".join(parts)


def format_lock_override_prompt_hint(
    scale: str = "medium",
    overrides: dict[str, Any] | None = None,
) -> str:
    """Short generation hint when artist loosened/tightened locks mid-session."""
    bits: list[str] = []
    for row in resolve_dim_lock_levels(scale, overrides):
        if not row["changed"]:
            continue
        direction = "放宽" if row["effective"] < row["base"] else "收紧"
        bits.append(
            f"{row['label']}锁定{direction}为{row['effective']}%（档位默认{row['base']}%）"
        )
    if not bits:
        return ""
    return "画师锁定微调：" + "；".join(bits)


def format_scale_artist_footer(
    scale: str = "medium",
    *,
    recompose_dir: str = "",
    scale_prof: dict[str, Any] | None = None,
    goal: str = "",
    ref_analysis: str = "",
    ref_image: str = "",
    module: str = "",
    dim_lock_overrides: dict[str, Any] | None = None,
) -> str:
    """
    Artist-facing footer: per-dimension lock % (+ base→effective when artist fine-tuned).
    Judge dim_weights % are demoted to a small internal note (not the main message).
    """
    s = (scale or "medium").strip().lower()
    if s not in CONVERGE_SCALE_PROFILES:
        s = "medium"
    # Also scrape goal for one-shot overrides if not already in dim_lock_overrides
    ov = merge_dim_lock_overrides(s, dim_lock_overrides, goal or "")
    prof = scale_prof or get_converge_scale_profile(
        s,
        recompose_dir=recompose_dir,
        goal=goal,
        ref_analysis=ref_analysis,
        ref_image=ref_image,
        module=module,
    )
    label = _SCALE_LABEL_ZH.get(s, str(prof.get("label") or s))
    scale_title = s.upper() if s != "recompose" else "Recompose"
    budget = str(prof.get("next_fix_budget") or "").strip() or "（见档位合同）"
    directive = str(prof.get("prompt_directive") or "").strip()
    hint = str(prof.get("best_direction_hint") or SCALE_BEST_DIRECTION_HINTS.get(s) or "").strip()
    thr = float(prof.get("target_score_threshold") or DEFAULT_THRESHOLD)
    weights_line = format_dim_weights_zh(prof.get("dim_weights") or {})
    summary = format_dim_lock_summary_zh(s, ov)
    changed = [r for r in resolve_dim_lock_levels(s, ov) if r["changed"]]
    lines = [
        "#### 🎚️ 本局档位合同（六维锁定%表 · 画师据此判断大改空间）",
        "",
        f"**目前是 {scale_title} 档**：{label}。"
        + ("（已含画师口头微调）" if changed else ""),
        f"一览：`{summary}`",
        "",
        "下表 **六维全部列出**（有效% · 本档默认% · 相对增减 ±%），方便对照往哪调；未改的维显示 **+0%**：",
        "",
    ]
    lines.extend(format_dim_lock_levels_zh(s, ov))
    lines.append("")
    lines.append(f"- **改动预算**：{budget} · 停机线 `>= {thr:.2f}`")
    if directive:
        lines.append(f"- **本档指令骨架**：{directive}")
    lock_hint = format_lock_override_prompt_hint(s, ov)
    if lock_hint:
        lines.append(f"- **本局锁定微调**：{lock_hint}")
    if s == "recompose" and (recompose_dir or prof.get("recompose_dir")):
        lines.append(f"- **改构图方向**：`{recompose_dir or prof.get('recompose_dir')}`")
    if hint:
        lines.append(f"- **本档优选微调**：{hint}")
    lines.extend(
        [
            "",
            "> 💬 **画师可写一句**（对照上表点名维度）：",
            "> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`",
            "",
            f"<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：{weights_line}</small>",
        ]
    )
    return "\n".join(lines)


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


