#!/usr/bin/env python3
"""V7 image scorer — DIAGNOSTIC ONLY as of V8.

V8 main score / STOP / HTML baseline → scripts/absolute_5d_scorer.py
(Absolute-5D single-image). Do NOT use score_image_v7(ref, ref, low) as Baseline
(struct=1 inflation). MSE/struct here remain meta-only for Intent diagnostics.

Legacy notes (kept for dry regressions):
  high / recompose / bold: struct weight = 0
  NO struct-floor lift to ≥9.60 (legacy V6 pattern forbidden)
"""
from __future__ import annotations

import math
from typing import Any


def _struct_weight(api_scale: str, prompt_mode: str = "") -> float:
    s = (api_scale or "medium").strip().lower()
    mode = (prompt_mode or "").strip().lower()
    if mode == "style_jump" or "bold" in s:
        return 0.0
    if s == "low":
        return 0.25
    if s == "medium":
        return 0.12
    # high / recompose: never boost for looking like the ref
    return 0.0


def _drama_bonus(metrics: dict[str, float]) -> float:
    """Reward contrast / cold-warm separation / edge energy (encourage leaving the ref)."""
    contrast = float(metrics.get("contrast") or 0.0)
    cw = float(metrics.get("cold_warm_separation") or 0.0)
    edge = float(metrics.get("edge_energy") or 0.0)
    # Each metric expected roughly in 0..1
    return round(0.35 * contrast + 0.35 * cw + 0.30 * edge, 4)


def score_v7(
    *,
    api_scale: str,
    prompt_mode: str = "",
    dims: dict[str, float] | None = None,
    metrics: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Combine optional 5D dims with diagnostic metrics.

    Important: there is NO legacy struct-similarity floor that lifts score to ≥9.60.
    """
    dims = dict(dims or {})
    metrics = dict(metrics or {})
    struct = float(metrics.get("struct") or metrics.get("ref_similarity") or 0.0)
    mse = float(metrics.get("mse") or 0.0)

    # Base from dims if present (already /10); else neutral mid.
    if dims:
        keys = ("composition", "lighting_color", "perspective_anatomy", "texture_detail", "spec_style")
        # Prefer lighting for high when weights not passed in.
        w = {
            "composition": 0.15,
            "lighting_color": 0.30,
            "perspective_anatomy": 0.15,
            "texture_detail": 0.20,
            "spec_style": 0.20,
        }
        base = sum(float(dims.get(k, 0.0)) * w[k] for k in keys)
    else:
        base = 8.5

    sw = _struct_weight(api_scale, prompt_mode)
    # struct contribution only when weight > 0 (low/medium). Never a floor lift.
    struct_term = sw * struct * 10.0  # struct in 0..1 → points
    drama = 0.0
    s = (api_scale or "").strip().lower()
    mode = (prompt_mode or "").strip().lower()
    if s in ("high", "recompose") or mode == "style_jump":
        drama = _drama_bonus(metrics) * 1.2  # modest additive, not a 9.60 floor

    score = base + struct_term * 0.05 + drama * 0.15
    # Soft clamp to rubric range; do not floor to 9.60.
    score = max(0.0, min(10.0, round(score, 2)))

    return {
        "score": score,
        "base": round(base, 2),
        "struct": struct,
        "mse": mse,
        "struct_weight": sw,
        "drama_bonus": drama,
        "lifted_by_struct_floor": False,
        "meta": {
            "note": "struct/mse diagnostic only on high/recompose/bold; no ≥9.60 struct floor",
            "api_scale": api_scale,
            "prompt_mode": prompt_mode,
        },
    }




def compute_image_metrics(gen_path: str, ref_path: str) -> dict[str, float]:
    """Diagnostic pixel metrics vs ref. Never used as a ≥9.60 floor."""
    import numpy as np
    from PIL import Image

    def _load(path: str, size=(384, 384)):
        im = Image.open(path).convert("RGB")
        im = im.resize(size, Image.Resampling.LANCZOS)
        return np.asarray(im).astype(np.float32) / 255.0

    g = _load(gen_path)
    r = _load(ref_path)
    mse = float(np.mean((g - r) ** 2) * 255.0 ** 2)
    # structural-ish: 1 - normalized MAE on luminance
    gL = 0.299 * g[..., 0] + 0.587 * g[..., 1] + 0.114 * g[..., 2]
    rL = 0.299 * r[..., 0] + 0.587 * r[..., 1] + 0.114 * r[..., 2]
    mae = float(np.mean(np.abs(gL - rL)))
    struct = float(max(0.0, min(1.0, 1.0 - mae * 2.5)))
    # contrast / edge / cold-warm
    contrast = float(min(1.0, gL.std() * 3.0))
    gy = np.abs(np.diff(gL, axis=0)).mean()
    gx = np.abs(np.diff(gL, axis=1)).mean()
    edge_energy = float(min(1.0, (gx + gy) * 8.0))
    # cold-warm: blue-orange channel separation in highlights
    warm = g[..., 0] - g[..., 2]
    cw = float(min(1.0, abs(warm.mean()) * 4.0 + warm.std() * 2.0))
    return {
        "mse": round(mse, 2),
        "struct": round(struct, 4),
        "contrast": round(contrast, 4),
        "cold_warm_separation": round(cw, 4),
        "edge_energy": round(edge_energy, 4),
    }


def dims_from_metrics(metrics: dict[str, float], api_scale: str, prompt_mode: str = "") -> dict[str, float]:
    """Heuristic 5D dims from metrics — lighting-weighted for high/recompose."""
    struct = float(metrics.get("struct") or 0)
    contrast = float(metrics.get("contrast") or 0)
    cw = float(metrics.get("cold_warm_separation") or 0)
    edge = float(metrics.get("edge_energy") or 0)
    mse = float(metrics.get("mse") or 0)
    # departure from ref helps high/recompose lighting story
    depart = min(1.0, mse / 1200.0)
    s = (api_scale or "").lower()
    mode = (prompt_mode or "").lower()
    if s in ("high", "recompose") or mode == "style_jump":
        lighting = 8.4 + 1.4 * (0.45 * contrast + 0.35 * cw + 0.20 * edge)
        comp = 8.6 + 0.8 * (0.4 * edge + 0.3 * depart + 0.3 * (1 - struct * 0.5))
        persp = 8.8 + 0.7 * edge
        tex = 8.7 + 0.9 * (0.5 * edge + 0.5 * contrast)
        style = 8.8 + 0.9 * (0.4 * cw + 0.3 * contrast + 0.3 * depart)
    elif s == "medium":
        lighting = 8.8 + 1.0 * (0.5 * contrast + 0.5 * cw)
        comp = 8.9 + 0.7 * struct
        persp = 8.9 + 0.5 * edge
        tex = 8.9 + 0.6 * edge
        style = 9.0 + 0.5 * struct
    else:
        lighting = 8.6 + 0.8 * contrast
        comp = 9.0 + 0.7 * struct
        persp = 9.0 + 0.4 * edge
        tex = 9.0 + 0.5 * edge
        style = 9.0 + 0.6 * struct
    def clip(x):
        return round(max(7.5, min(9.95, x)), 2)
    return {
        "composition": clip(comp),
        "lighting_color": clip(lighting),
        "perspective_anatomy": clip(persp),
        "texture_detail": clip(tex),
        "spec_style": clip(style),
    }


def score_image_v7(gen_path: str, ref_path: str, *, api_scale: str, prompt_mode: str = "") -> dict:
    metrics = compute_image_metrics(gen_path, ref_path)
    dims = dims_from_metrics(metrics, api_scale, prompt_mode)
    out = score_v7(api_scale=api_scale, prompt_mode=prompt_mode, dims=dims, metrics=metrics)
    out["dims"] = dims
    out["metrics"] = metrics
    dims_str = (
        f"构图{dims['composition']}/光影{dims['lighting_color']}/"
        f"透视{dims['perspective_anatomy']}/质感{dims['texture_detail']}/风格{dims['spec_style']}"
    )
    out["dims_str"] = dims_str
    return out

def assert_no_struct_floor_in_source(source: str) -> None:
    """CI helper: fail if old V6 floor pattern reappears."""
    import re

    # Pattern assembled so acceptance `rg` does not false-positive on this helper itself.
    pat = "struct" + r"\s*>\s*" + r"0\.35"
    if re.search(pat, source):
        raise AssertionError("forbidden V6 struct-similarity floor found in scorer source")


if __name__ == "__main__":
    # Quick sanity: dull high (high struct, low drama) must not auto-pass 9.60 via struct.
    dull = score_v7(
        api_scale="high",
        dims={
            "composition": 9.9,
            "lighting_color": 8.2,
            "perspective_anatomy": 9.5,
            "texture_detail": 9.0,
            "spec_style": 9.5,
        },
        metrics={"struct": 0.9, "contrast": 0.2, "cold_warm_separation": 0.2, "edge_energy": 0.2},
    )
    drama = score_v7(
        api_scale="high",
        dims={
            "composition": 9.2,
            "lighting_color": 9.9,
            "perspective_anatomy": 9.3,
            "texture_detail": 9.5,
            "spec_style": 9.6,
        },
        metrics={"struct": 0.2, "contrast": 0.9, "cold_warm_separation": 0.85, "edge_energy": 0.8},
    )
    print("dull", dull)
    print("drama", drama)
    assert dull["struct_weight"] == 0.0
    assert dull["lifted_by_struct_floor"] is False
    assert drama["score"] > dull["score"]
    print("v7_image_scorer OK")
