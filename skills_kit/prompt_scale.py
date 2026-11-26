"""Converge scale profiles and prompt directive helpers."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst
from core.scale_constants import (  # noqa: F401  moved to core, re-exported
    APP_ICON_DIM_WEIGHTS,
    DEFAULT_MAX_ROUNDS,
    DEFAULT_THRESHOLD,
    FAST_SOFT_THRESHOLD,
    MIN_IMAGE_BYTE_ENTROPY,
    MIN_IMAGE_EDGE_PX,
    UI_DEDICATED_DIM_WEIGHTS,
)
from core.injection_filter import (  # noqa: F401
    _CLAUSE_NEG,
    _clause_affirmed,
    _drop_ban_token,
    _drop_pref_token,
    drop_opposed_injections,
)
from .scale_profile import (  # noqa: F401  moved to scale_profile, re-exported
    _CASE_ID_STYLE,
    CONVERGE_SCALE_PROFILES,
    _forbidden_families,
    _infer_case_style_and_subject,
    _match_style_keywords,
    _merge_low_forbidden,
    get_converge_scale_profile,
)



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


def directive_survives_in_prompt(directive: str, prompt: str) -> bool:
    """True when the scale line is still in the prompt, or the brief removed it on purpose."""
    directive = (directive or "").strip()
    prompt = prompt or ""
    if not directive:
        return True
    if not prompt.strip():
        return False
    if directive in prompt:
        return True
    surviving = drop_opposed_injections(directive, brief=prompt).strip(" |")
    if not surviving:
        return True
    return surviving in prompt


def _icon_hero_grid(path: Path) -> tuple[int, int, int, int, int, int, int, int, int] | None:
    """Hero box on the coarse grid: minx, miny, maxx, maxy, gw, gh, step, w, h."""
    try:
        from PIL import Image
    except ImportError:
        return None
    im = Image.open(path).convert("RGB")
    w, h = im.size
    if w < 8 or h < 8:
        return None
    px = im.load()
    step = max(1, min(w, h) // 160)
    gw = (w + step - 1) // step
    gh = (h + step - 1) // step

    def col(gx: int, gy: int) -> tuple[int, int, int]:
        return px[min(gx * step, w - 1), min(gy * step, h - 1)]

    def near(a: tuple[int, int, int], b: tuple[int, int, int], tol: int = 46) -> bool:
        return abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2]) <= tol

    seen = bytearray(gw * gh)
    stack: list[tuple[int, int]] = []
    for gx, gy in ((0, 0), (gw - 1, 0), (0, gh - 1), (gw - 1, gh - 1)):
        i = gy * gw + gx
        if not seen[i]:
            seen[i] = 1
            stack.append((gx, gy))
    while stack:
        gx, gy = stack.pop()
        base = col(gx, gy)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = gx + dx, gy + dy
            if nx < 0 or ny < 0 or nx >= gw or ny >= gh:
                continue
            i = ny * gw + nx
            if seen[i] or not near(col(nx, ny), base):
                continue
            seen[i] = 1
            stack.append((nx, ny))
    minx, miny, maxx, maxy = gw, gh, 0, 0
    hit = False
    for gy in range(gh):
        row = gy * gw
        for gx in range(gw):
            if seen[row + gx]:
                continue
            hit = True
            if gx < minx:
                minx = gx
            if gy < miny:
                miny = gy
            if gx > maxx:
                maxx = gx
            if gy > maxy:
                maxy = gy
    if not hit:
        return None
    return minx, miny, maxx, maxy, gw, gh, step, w, h


def icon_subject_span(path: Path) -> tuple[float, float] | None:
    """Width and height of the hero box, as fractions of the canvas.

    Background is whatever can be walked from the four corners, including a
    smooth gradient. The box size is not the edge-crop test.
    """
    box = _icon_hero_grid(path)
    if not box:
        return None
    minx, miny, maxx, maxy, _gw, _gh, step, w, h = box
    return (maxx - minx + 1) * step / w, (maxy - miny + 1) * step / h


def icon_stage_margins(path: Path) -> tuple[float, float, float, float] | None:
    """Empty ground on the left, right, top and bottom, as fractions of the canvas.

    A store icon is cropped when every side is near zero and ground survives
    only in the corners. A centered box at 76% still has a stage on all four sides.
    """
    box = _icon_hero_grid(path)
    if not box:
        return None
    minx, miny, maxx, maxy, _gw, _gh, step, w, h = box
    left = minx * step / w
    right = max(0.0, 1.0 - (maxx + 1) * step / w)
    top = miny * step / h
    bottom = max(0.0, 1.0 - (maxy + 1) * step / h)
    return left, right, top, bottom


def compose_continuation_prompt(
    fix: str,
    scale_prof: dict[str, Any],
    *,
    stub_notes: list[str] | None = None,
    locks: list[str] | None = None,
    pad_image: str = "",
    release_margin: bool = False,
) -> str:
    """Round 2+: the pad is the previous plate. Name one repair; do not restate the scene."""
    from .must_fix import sanitize_continuation_fix

    scale = str(scale_prof.get("scale") or "")
    directive = strip_affirmative_locks_from_prompt(
        str(scale_prof.get("prompt_directive") or "").strip(),
        scale=scale,
    )
    safe_fix = sanitize_continuation_fix(
        strip_redline_tags_from_generation_text(fix or "").strip()
    )
    one = strip_affirmative_locks_from_prompt(safe_fix, scale=scale)
    if not one:
        one = "只补这一张里还没到位的那一处"
    direction = str(scale_prof.get("recompose_dir") or "").strip()
    keep_camera = ""
    if scale == "recompose" and direction:
        keep_camera = f"机位保持指定方向：{direction}。"
    lock_bits = [str(x).strip() for x in (locks or []) if str(x).strip()]
    lock_pin = ""
    if lock_bits:
        lock_pin = "L1锁必须保住：" + "；".join(lock_bits[:8]) + "。"
    pad_path = (pad_image or "").strip()
    pad_clause = f"垫这张成图：{pad_path}。" if pad_path else "垫图是目前分数最高的那张成图。"
    if release_margin:
        keep = "主体、配色和边框保持垫图。四周留白不算要保持的内容，外轮廓顶到四边，底色只留在四角。"
    else:
        keep = "没点名的地方保持垫图。"
    edit = (
        f"{keep_camera}{lock_pin}"
        f"{pad_clause}只改这一处：{one}。{keep}"
        "禁止借改点换题材/换品类/换技能。"
    )
    directive = drop_opposed_injections(directive, brief=f"{one}\n{lock_pin}")
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
    directive = drop_opposed_injections(directive, brief=body)
    tail = drop_opposed_injections(_constraint_tail(scale_prof), brief=body)
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
    "flawlessness": "无瑕度",
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
    "无瑕度": "flawlessness",
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
        r"(构图|光影色彩|光影|透视与解剖|透视解剖|透视|解剖|质感|材质|规格与风格|规格风格|风格|规格|无瑕度|无瑕疵|"
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
        r"(构图|光影色彩|光影|透视与解剖|透视解剖|透视|解剖|质感|材质|规格与风格|规格风格|风格|规格|无瑕度|无瑕疵)"
        r".{0,10}(再?松一点|松一些|放宽|松点儿|放松|再松)",
        raw,
    ):
        key = _DIM_ALIAS_TO_KEY.get(m.group(1))
        if key and key not in found:
            found[key] = max(0, _eff(key) - LOCK_RELAX_STEP)
    for m in re.finditer(
        r"(构图|光影色彩|光影|透视与解剖|透视解剖|透视|解剖|质感|材质|规格与风格|规格风格|风格|规格|无瑕度|无瑕疵)"
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






