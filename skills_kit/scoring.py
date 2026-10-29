"""6D dimension parsing (5 craft dims + flawlessness) and score-inflation audit."""
from __future__ import annotations

import json
import math
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


def _is_icon_prop_5d_context(dims_str: str = "", module: str = "") -> bool:
    mod = (module or "").strip().lower()
    if mod.startswith("icon.prop") or mod in ("icon.item", "icon.c"):
        return True
    s = dims_str or ""
    markers = ("剪影识别", "描边色板", "棚拍", "无字")
    return sum(1 for kw in markers if kw in s) >= 2


def _is_icon_svg_5d_context(dims_str: str = "", module: str = "") -> bool:
    mod = (module or "").strip().lower()
    if mod.startswith("icon.svg") or mod in ("icon.b", "icon.linear"):
        return True
    s = dims_str or ""
    markers = ("笔画一致", "视觉重量", "光学居中", "留白", "功能识别")
    return sum(1 for kw in markers if kw in s) >= 2


def _is_ui_5d_context(dims_str: str = "", module: str = "") -> bool:
    mod = (module or "").strip().lower()
    if mod == "ui" or mod.startswith("ui."):
        return True
    s = (dims_str or "").lower()
    ui_markers = ("九宫格", "9-slice", "状态族", "套件", "透明底", "rgba", "合规")
    return sum(1 for kw in ui_markers if kw in s) >= 2


_CLAUSE_PUNCT = "，。；但"
_CLAUSE_CLEAR = re.compile(
    r"已彻底解决|彻底解决|已经解决|已解决|解决了|已修复|已消除|已去掉|不再出现|未出现|并未出现|并未发现|严禁|禁止|不得出现|不得有"
)
_CLAUSE_STILL_BROKEN = re.compile(
    r"(?:不是已经|没有已经|并非已经|并未已经|不是已)解决|"
    r"(?:没有|没能|未能|无法|需要|并未|还不|仍未|尚未|未|不|没)(?:彻底)?解决"
)
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


def _clause_fixed(low: str, index: int, key_len: int, clause: str) -> bool:
    """A defect is gone when this clause says so, or the next 但-clause is only a fix."""
    if _CLAUSE_STILL_BROKEN.search(clause):
        return False
    if re.search(r"(?:不是|没有|并非|并未).{0,12}解决", clause):
        return False
    if re.search(r"(?:解决了|已经解决|已解决|已修复).{0,6}(?:不了|又出现|又不|没有|不|没|吗)", clause):
        return False
    if _CLAUSE_CLEAR.search(clause):
        return True
    end = index + key_len
    while end < len(low) and low[end] not in _CLAUSE_PUNCT:
        end += 1
    if end >= len(low) or low[end] not in _CLAUSE_PUNCT:
        return False
    nxt = low[end + 1 :]
    for ch in _CLAUSE_PUNCT:
        if ch == "但":
            continue
        cut = nxt.find(ch)
        if cut >= 0:
            nxt = nxt[:cut]
    nxt_s = nxt.strip()
    if nxt_s.startswith("但是"):
        nxt_s = nxt_s[2:].strip()
    elif nxt_s.startswith("但") or nxt_s.startswith("是"):
        nxt_s = nxt_s[1:].strip()
    return bool(re.fullmatch(r"(?:已经解决了?|已解决了?|解决了|已修复了?|已消除了?)", nxt_s))


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
            if _clause_fixed(low, i, len(k), clause):
                start = i + len(k)
                continue
            if _locally_negated(low, i):
                start = i + len(k)
                continue
            hits.append(kw)
            break
    return hits


def weighted_harmonic(
    scores: dict[str, float],
    weights: dict[str, float],
    keys: tuple[str, ...],
) -> float | None:
    """Weighted harmonic mean. Weights on `keys` are renormalized to 1."""
    from .medium_family import weighted_harmonic as _harmonic

    return _harmonic(scores, weights, keys)


def weighted_geometric(
    scores: dict[str, float],
    weights: dict[str, float],
    keys: tuple[str, ...],
) -> float | None:
    """Weighted geometric mean. Weights on `keys` are renormalized to 1."""
    if any(k not in scores for k in keys):
        return None
    wsum = sum(float(weights.get(k) or 0) for k in keys)
    if wsum <= 0:
        return None
    acc = 0.0
    for k in keys:
        x = float(scores[k])
        if x <= 0:
            return 0.0
        acc += (float(weights.get(k) or 0) / wsum) * math.log(x)
    return round(math.exp(acc), 2)


def apply_hurdles(
    score: float,
    scores: dict[str, float],
    hurdles: tuple[tuple[str, float], ...],
) -> tuple[float, dict[str, Any] | None]:
    """If a hurdle dimension is under its floor, the official score becomes that dimension."""
    hit: dict[str, Any] | None = None
    for key, floor in hurdles:
        if key not in scores:
            continue
        val = float(scores[key])
        if val < float(floor) and (hit is None or val < float(hit["value"])):
            hit = {"key": key, "floor": float(floor), "value": val}
    if hit:
        score = min(float(score), float(hit["value"]))
    return round(float(score), 2), hit


def _bundle_score(
    parsed: dict[str, float],
    weights: dict[str, float],
    score_keys: tuple[str, ...],
    hurdles: tuple[tuple[str, float], ...],
    mode: str,
) -> dict[str, Any] | None:
    use_weights = dict(weights)
    use_keys = score_keys
    if "flawlessness" in parsed:
        craft = [k for k in score_keys if k != "flawlessness"]
        base = {k: float(weights.get(k) or 0) for k in craft}
        total = sum(base.values()) or 1.0
        use_weights = {k: 0.75 * base[k] / total for k in craft}
        use_weights["flawlessness"] = 0.25
        use_keys = tuple(craft) + ("flawlessness",)
    mean = weighted_harmonic(parsed, use_weights, use_keys)
    if mean is None:
        return None
    official, hit = apply_hurdles(mean, parsed, hurdles)
    out: dict[str, Any] = {
        "parsed": parsed,
        "weighted_score": official,
        "geometric_score": mean,
        "harmonic_score": mean,
        "rubric_mode": mode,
    }
    if hit:
        out["hurdle"] = hit
    return out


# UI: pipeline is scored and can veto, but it is not inside the product.
UI_SCORE_KEYS = (
    "style_palette",
    "nine_slice_structure",
    "lighting_material",
    "state_suite_cohesion",
)
UI_HURDLES = (("nine_slice_structure", 7.5), ("rgba_pipeline_compliance", 8.0))
ICON_A_SCORE_KEYS = (
    "glyph_silhouette",
    "squircle_safe_zone",
    "tactile_lighting",
    "multisize_adaptive",
    "palette_purity",
)
ICON_A_HURDLES = (("glyph_silhouette", 8.0), ("squircle_safe_zone", 8.0))
ICON_PROP_WEIGHTS = {"silhouette": 0.30, "stroke_palette": 0.20, "studio_light": 0.20}
ICON_PROP_SCORE_KEYS = ("silhouette", "stroke_palette", "studio_light")
ICON_PROP_HURDLES = (("silhouette", 8.0), ("alpha", 8.0), ("no_text", 8.0))
ICON_SVG_WEIGHTS = {
    "stroke_consistency": 0.25,
    "visual_weight": 0.25,
    "optical_center": 0.25,
    "recognizability": 0.25,
}
ICON_SVG_SCORE_KEYS = tuple(ICON_SVG_WEIGHTS)
ICON_SVG_HURDLES = (("stroke_consistency", 8.0), ("recognizability", 8.0))
GENERAL_5D_KEYS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
)


_KV_5D_ALIAS = {
    "composition": "composition",
    "comp": "composition",
    "lighting_color": "lighting_color",
    "lighting": "lighting_color",
    "light": "lighting_color",
    "color": "lighting_color",
    "perspective_anatomy": "perspective_anatomy",
    "perspective": "perspective_anatomy",
    "anatomy": "perspective_anatomy",
    "craft": "perspective_anatomy",
    "texture_detail": "texture_detail",
    "texture": "texture_detail",
    "detail": "texture_detail",
    "spec_style": "spec_style",
    "style": "spec_style",
    "flawlessness": "flawlessness",
    "flawless": "flawlessness",
}


def _parse_kv_5d(dims_str: str, weights: dict[str, float]) -> dict[str, Any] | None:
    pairs = re.findall(
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([0-9]+(?:\.[0-9]+)?)",
        dims_str or "",
    )
    if len(pairs) < 4:
        return None
    bucket: dict[str, list[float]] = {}
    pair_keys = {key.lower() for key, _val in pairs}
    has_style_key = bool(pair_keys & {"style", "spec_style"})
    for key, val in pairs:
        k = key.lower()
        if k == "spec":
            # Bare spec: style dim unless a real style key is already present
            # (legacy four-key: style= + spec= → spec means perspective).
            dest = "perspective_anatomy" if has_style_key else "spec_style"
        else:
            dest = _KV_5D_ALIAS.get(k)
        if dest is None:
            continue
        bucket.setdefault(dest, []).append(float(val))
    parsed = {k: round(sum(v) / len(v), 2) for k, v in bucket.items()}
    needed = ("composition", "lighting_color", "perspective_anatomy", "texture_detail", "spec_style")
    # Only the old four-key dialect may invent lighting. Any other missing dim fails closed.
    if (
        "lighting_color" not in parsed
        and pair_keys <= {"style", "comp", "spec", "detail"}
        and all(k in parsed for k in ("composition", "perspective_anatomy", "texture_detail", "spec_style"))
    ):
        others = [parsed[k] for k in ("composition", "perspective_anatomy", "texture_detail", "spec_style")]
        parsed["lighting_color"] = round(sum(others) / len(others), 2)
    if any(k not in parsed for k in needed):
        return None
    from .medium_family import GENERAL_6D_KEYS, ensure_general_weights

    w6 = ensure_general_weights(weights)
    if "flawlessness" in parsed:
        mean = weighted_harmonic(parsed, w6, GENERAL_6D_KEYS)
        kept = GENERAL_6D_KEYS
    else:
        mean = weighted_harmonic(parsed, w6, needed)
        kept = needed
    return {
        "parsed": {k: parsed[k] for k in kept if k in parsed},
        "weighted_score": mean,
        "geometric_score": mean,
        "harmonic_score": mean,
        "rubric_mode": "general_6d" if "flawlessness" in parsed else "general_5d",
    }


def _parse_skill_additive(dims_str: str) -> dict[str, Any] | None:
    """Old slip only: 风格2.5 + 结构2.5 + 光影2.0 + 合规1.5 + 还原1.5, summed to 10.

    A 10-point reading of those same five labels is scaled back into the caps.
    Strings that name 套件 / 九宫格 / 剪影 / 识别度 return None and use the geometric rubric.
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
    # Dedicated UI / icon strings must not be folded back into the old 10-point sum.
    if re.search(
        r"(?:套件|九宫格|剪影识别|笔画一致|棚拍|识别度|安全区|风格色板|光影材质|管线合规|构图叙事)",
        probe,
    ):
        return None
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
    parsed = _attach_flawlessness(raw, probe)
    flaw = parsed.get("flawlessness")
    if flaw is not None:
        craft10 = min(10.0, float(total))
        flaw_f = float(flaw)
        if craft10 <= 0 or flaw_f <= 0:
            total = 0.0
        else:
            total = round(1.0 / (0.75 / craft10 + 0.25 / flaw_f), 2)
    return {
        "parsed": parsed,
        "weighted_score": total,
        "rubric_mode": "skill_additive_5d",
    }


def _read_labeled(dims_str: str, patterns: dict[str, tuple[str, float]]) -> dict[str, float]:
    raw: dict[str, float] = {}
    for key, (pat, _cap) in patterns.items():
        m = re.search(pat, dims_str or "", flags=re.IGNORECASE)
        if m:
            raw[key] = float(m.group(1))
    return raw


def _attach_flawlessness(raw: dict[str, float], dims_str: str) -> dict[str, float]:
    m = re.search(
        r"(?:无瑕疵|无暇|flawlessness|flawless)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        dims_str or "",
        flags=re.IGNORECASE,
    )
    if not m:
        return raw
    out = dict(raw)
    out["flawlessness"] = float(m.group(1))
    return out


def _to_ten_point(raw: dict[str, float], patterns: dict[str, tuple[str, float]]) -> dict[str, float]:
    subscale = all(raw[k] <= patterns[k][1] + 0.05 for k in raw)
    out: dict[str, float] = {}
    for key, val in raw.items():
        cap = patterns[key][1]
        out[key] = round((val / cap) * 10.0, 2) if subscale else val
    return out


def parse_5d_dims(
    dims_str: str,
    weights: dict[str, float] | None = None,
    *,
    module: str = "",
) -> dict[str, Any]:
    """
    Parse a score string and compute the official weighted harmonic mean.
    Supports:
    1) General art / character / concept 6D: 构图 / 光影 / 透视 / 质感 / 风格 / 无瑕疵（无瑕疵占 25%）
    2) Dedicated /pmem-ui rubric when module starts with 'ui' or UI keywords are present:
       工艺项占 75%，无瑕疵占 25%。Automatically normalizes 2.5/2.5/2.0/1.5/1.5 point scales or 10-point scales to /10.0.
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

    if _is_icon_prop_5d_context(dims_str, module=module):
        prop_patterns = {
            "silhouette": (r"(?:剪影识别|剪影)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 3.0),
            "stroke_palette": (r"(?:描边色板|描边)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
            "studio_light": (r"(?:棚拍光|棚拍)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
            "alpha": (r"(?:透明底|脏底)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
            "no_text": (r"(?:无字|文字)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
        }
        raw_prop = _read_labeled(dims_str, prop_patterns)
        if len(raw_prop) == 5:
            bundled = _bundle_score(
                _attach_flawlessness(_to_ten_point(raw_prop, prop_patterns), dims_str),
                ICON_PROP_WEIGHTS,
                ICON_PROP_SCORE_KEYS,
                ICON_PROP_HURDLES,
                "icon_prop_5d",
            )
            if bundled is not None:
                return bundled

    if _is_icon_svg_5d_context(dims_str, module=module):
        svg_patterns = {
            "stroke_consistency": (r"(?:笔画一致|笔画)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "visual_weight": (r"(?:视觉重量|重量)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "optical_center": (r"(?:光学居中|留白)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "recognizability": (r"(?:功能识别|能对上|识别)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
        }
        raw_svg = _read_labeled(dims_str, svg_patterns)
        if len(raw_svg) == 4:
            bundled = _bundle_score(
                _attach_flawlessness(_to_ten_point(raw_svg, svg_patterns), dims_str),
                ICON_SVG_WEIGHTS,
                ICON_SVG_SCORE_KEYS,
                ICON_SVG_HURDLES,
                "icon_svg_5d",
            )
            if bundled is not None:
                return bundled

    if _is_app_icon_5d_context(dims_str, module=module):
        icon_patterns = {
            "glyph_silhouette": (r"(?:识别度|品牌符号|符号|小尺寸|glyph|silhouette)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "squircle_safe_zone": (r"(?:安全区|圆角遮罩|1024母版|母版|safe_zone|squircle)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "tactile_lighting": (r"(?:光影质感|微立体|光影|材质|tactile|lighting)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
            "multisize_adaptive": (r"(?:多尺寸合规|多尺寸|深浅色|自适应|multisize|adaptive)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
            "palette_purity": (r"(?:色板纯粹|无文字红线|色板|纯粹|palette|purity)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
        }
        raw_vals_ic: dict[str, float] = {}
        for k, (pat, max_pt) in icon_patterns.items():
            m = _re.search(pat, dims_str or "", flags=_re.IGNORECASE)
            if m:
                raw_vals_ic[k] = float(m.group(1))
        if len(raw_vals_ic) == 5:
            bundled = _bundle_score(
                _attach_flawlessness(_to_ten_point(raw_vals_ic, icon_patterns), dims_str),
                APP_ICON_DIM_WEIGHTS,
                ICON_A_SCORE_KEYS,
                ICON_A_HURDLES,
                "app_icon_5d",
            )
            if bundled is not None:
                return bundled

    dedicated_ui = bool(
        _re.search(r"(?:风格色板|光影材质|管线合规|构图叙事|套件|九宫格)", dims_str or "")
    )
    if _is_ui_5d_context(dims_str, module=module) or dedicated_ui:
        ui_patterns = {
            "style_palette": (r"(?:风格色板|风格|色板|style_palette)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.5),
            "nine_slice_structure": (
                r"(?:九宫格|9-slice|结构透视|构图叙事(?:与透视)?|结构|nine_slice)"
                r"[^0-9]*([0-9]+(?:\.[0-9]+)?)",
                2.5,
            ),
            "lighting_material": (r"(?:光影材质|光影|材质|lighting_material)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 2.0),
            "rgba_pipeline_compliance": (r"(?:透明底|rgba|管线合规|合规|红线|pipeline)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
            "state_suite_cohesion": (r"(?:状态族|套件一致性|套件|状态|一致性|还原|state_suite)[^0-9]*([0-9]+(?:\.[0-9]+)?)", 1.5),
        }
        raw_vals: dict[str, float] = {}
        for k, (pat, max_pt) in ui_patterns.items():
            m = _re.search(pat, dims_str or "", flags=_re.IGNORECASE)
            if m:
                raw_vals[k] = float(m.group(1))
        if len(raw_vals) == 5:
            bundled = _bundle_score(
                _attach_flawlessness(_to_ten_point(raw_vals, ui_patterns), dims_str),
                UI_DEDICATED_DIM_WEIGHTS,
                UI_SCORE_KEYS,
                UI_HURDLES,
                "ui_5d",
            )
            if bundled is not None:
                return bundled

    w = weights or {
        "composition": 0.20,
        "lighting_color": 0.25,
        "perspective_anatomy": 0.20,
        "texture_detail": 0.20,
        "spec_style": 0.15,
    }
    # Do not let `spec` match the substring inside `perspective`.
    patterns = {
        "composition": r"(?:构图|composition)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "lighting_color": r"(?:光影|色彩|lighting)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "perspective_anatomy": r"(?:透视|解剖|结构|perspective|anatomy)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "texture_detail": r"(?:质感|肌理|细节|texture)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
        "spec_style": (
            r"(?:风格|规格|spec_style|"
            r"(?<![A-Za-z])spec(?![A-Za-z_])|"
            r"(?<![A-Za-z])style(?![A-Za-z_]))"
            r"[^0-9]*([0-9]+(?:\.[0-9]+)?)"
        ),
        "flawlessness": r"(?:无瑕疵|无暇|flawlessness|flawless)[^0-9]*([0-9]+(?:\.[0-9]+)?)",
    }
    parsed: dict[str, float] = {}
    for k, pat in patterns.items():
        m = _re.search(pat, dims_str or "", flags=_re.IGNORECASE)
        if m:
            parsed[k] = float(m.group(1))
    from .medium_family import GENERAL_6D_KEYS, ensure_general_weights

    w6 = ensure_general_weights(w)
    craft = GENERAL_5D_KEYS
    if all(k in parsed for k in craft):
        if "flawlessness" in parsed:
            mean = weighted_harmonic(parsed, w6, GENERAL_6D_KEYS)
            mode = "general_6d"
            kept = GENERAL_6D_KEYS
        else:
            mean = weighted_harmonic(parsed, w6, craft)
            mode = "general_5d"
            kept = craft
        return {
            "parsed": {k: parsed[k] for k in kept},
            "weighted_score": mean,
            "geometric_score": mean,
            "harmonic_score": mean,
            "rubric_mode": mode,
        }
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
                    f"检测到报送总分 ({float(raw_score):.2f}) 高于调和平均 ({float(weighted):.2f})，已改用调和平均"
                )
        calibrated = float(weighted)
    else:
        if raw_score is not None and float(raw_score) > 0:
            warnings.append("维度字符串无法解析，拒绝采用手填总分，本轮记 0 分")
        calibrated = 0.0

    limb_artifact_keywords = (
        "三只手", "多手", "第三只手", "多余的手", "多指", "六指", "多余肢体", "三条腿", "三条手臂", "三只胳膊",
        "多出一条", "多余刀鞘", "多余武器", "解剖错误", "肢体畸形", "手部畸形",
        "three hands", "3 hands", "extra hand", "extra hands", "extra limb", "extra limbs",
        "three arms", "3 arms", "extra arm", "mutated hand", "extra fingers", "fused fingers",
        "anatomical artifact", "extra weapon", "extra sheath",
    )
    defects_lower = (defects_str or "").lower()
    from .subject_lexicon import (
        clone_style_lock_new_subject_task,
        clone_subject_echo_marked,
        ui_shell_clone_task,
        ui_shell_echo_marked,
    )

    goal_blob = str(scale_prof.get("goal") or "")
    ref_blob = str(scale_prof.get("ref_analysis") or "")
    ref_img_blob = str(scale_prof.get("ref_image") or "")
    if ui_shell_clone_task(module=module, goal=goal_blob, ref_analysis=ref_blob):
        if ui_shell_echo_marked(defects_str or ""):
            warnings.append(
                "UI弹框母版回声拦截：内容区出现参考主体/礼盒等，禁止达标 (<=8.85)"
            )
            calibrated = min(calibrated, 8.85)
    if clone_style_lock_new_subject_task(
        module=module,
        goal=goal_blob,
        ref_analysis=ref_blob,
        ref_image=ref_img_blob,
    ):
        if clone_subject_echo_marked(defects_str or ""):
            warnings.append(
                "Clone 题材回声拦截：复制参考 prop 而非 brief 新主体，禁止达标 (<=8.85)"
            )
            calibrated = min(calibrated, 8.85)

    hit_limb = _keyword_hits(defects_lower, limb_artifact_keywords)
    if hit_limb:
        warnings.append(
            f"解剖/肢体硬伤一票否决拦截：检测到多手/多肢体/多余器物伪影 {hit_limb}，强制触发硬伤上限压分 (<=7.90) 并拒绝达标"
        )
        calibrated = min(calibrated, 7.90)

    severe_defect_keywords = (
        "画幅比例错误",
        "aspect ratio mismatch",
    )
    hit_kw = _keyword_hits(defects_lower, severe_defect_keywords)
    from .converge_policy import STYLE_INFLATION_IGNORE, infer_style_family

    style_family = infer_style_family(
        str(scale_prof.get("goal") or ""),
        module,
        str(scale_prof.get("ref_image") or ""),
    )
    ignored = STYLE_INFLATION_IGNORE.get(style_family) or set()
    if ignored:
        hit_kw = [h for h in hit_kw if h not in ignored]
    if hit_kw and calibrated > 9.0:
        warnings.append(
            f"反虚高拦截：缺陷栏包含关键短板词 {hit_kw}，禁止因基础完成度达标而给 9.0+ 虚高分，已触发严苛上限校准 (<=8.90)"
        )
        calibrated = min(calibrated, 8.90)

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


def calibrate_against_offline(
    calibrated: float,
    offline_score: float | None = None,
    coverage: float | None = None,
    *,
    judge_source: str = "",
    rubric_mode: str = "",
    module: str = "",
) -> dict[str, Any]:
    """Retired. Pixel offline scores are not computed and never change the official score."""
    del offline_score, coverage, judge_source, rubric_mode, module
    return {
        "calibrated_score": round(float(calibrated), 2),
        "capped": False,
        "warning": "",
    }



