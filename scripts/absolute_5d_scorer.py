#!/usr/bin/env python3
"""Offline Absolute-5D checklist scorer (gpt-6-sol quant rubric) — advisory only.

Contract: docs/gpt6sol_absolute_5d_quant_rubric.md
Human doc: docs/OFFLINE_ABSOLUTE_5D.md

Pixel path (this module): measurable proxies only; HEURISTIC_STOP_THRESHOLD=8.50
is a **batch/diagnostic band label**, never converge accept_threshold.

No-key converge path: Agent Absolute-5D via CLI dims @ LEGACY_SHOWCASE_STOP (9.50);
see skills_kit/absolute_5d_agent_rubric.py. Independent VLM preferred when keyed.

Scoring: each dim = 6 items × (0/1/2) × weight → P/100 → S=P/10;
hard caps; N/A excluded (renormalize); coverage reported.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

# Band label for diagnostics / batch reports only — NOT converge accept_threshold.
# Converge without independent VLM uses Agent Absolute-5D @ LEGACY_SHOWCASE_STOP (9.50).
HEURISTIC_STOP_THRESHOLD = 8.50
LEGACY_SHOWCASE_STOP = 9.50

SCORER_VERSION = "v9.1_audit_patch"
CONTRACT = "docs/gpt6sol_absolute_5d_quant_rubric.md"
AUDIT = "docs/offline_vs_vlm_gap_gpt6sol_audit.md"
# Rubric「合格」档 — used to shrink low-coverage dims (audit §聚合)
NEUTRAL_PRIOR = 7.0

_DIM_KEYS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
)

# Rubric §7.1 default (+ scale overrides). Offline often drops perspective via N/A.
_WEIGHTS: dict[str, dict[str, float]] = {
    "default": {
        "composition": 0.20,
        "lighting_color": 0.20,
        "perspective_anatomy": 0.25,
        "texture_detail": 0.15,
        "spec_style": 0.20,
    },
    "low": {
        "composition": 0.15,
        "lighting_color": 0.20,
        "perspective_anatomy": 0.25,
        "texture_detail": 0.25,
        "spec_style": 0.15,
    },
    "medium": {
        "composition": 0.20,
        "lighting_color": 0.20,
        "perspective_anatomy": 0.25,
        "texture_detail": 0.15,
        "spec_style": 0.20,
    },
    "high": {
        "composition": 0.15,
        "lighting_color": 0.20,
        "perspective_anatomy": 0.30,
        "texture_detail": 0.20,
        "spec_style": 0.15,
    },
    "recompose": {
        "composition": 0.25,
        "lighting_color": 0.15,
        "perspective_anatomy": 0.15,
        "texture_detail": 0.15,
        "spec_style": 0.30,
    },
}

# Per-dim item weights (sum 100) — rubric tables.
_ITEM_WEIGHTS: dict[str, list[tuple[str, float]]] = {
    "composition": [
        ("C1", 20), ("C2", 20), ("C3", 15), ("C4", 15), ("C5", 15), ("C6", 15),
    ],
    "lighting_color": [
        ("L1", 20), ("L2", 20), ("L3", 15), ("L4", 15), ("L5", 15), ("L6", 15),
    ],
    "perspective_anatomy": [
        ("P1", 20), ("P2", 15), ("P3", 20), ("P4", 20), ("P5", 15), ("P6", 10),
    ],
    "texture_detail": [
        ("T1", 20), ("T2", 20), ("T3", 15), ("T4", 20), ("T5", 15), ("T6", 10),
    ],
    "spec_style": [
        ("S1", 20), ("S2", 15), ("S3", 20), ("S4", 15), ("S5", 15), ("S6", 15),
    ],
}

# Min available item-weight inside a dim to keep the dim (else dim = N/A).
_DIM_MIN_ITEM_WEIGHT = 30.0
# Perspective needs real geometry — a lone P5 proxy is NOT enough (audit).
_DIM_MIN_ITEM_WEIGHT_PERSPECTIVE = 40.0
# Total weight coverage below this → score is reference-only (still returned).
_RANK_COVERAGE_FLOOR = 0.80


def _clip(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, float(x)))


def _r012(lo: float, mid: float, hi: float, value: float, *, higher_better: bool = True) -> int:
    """Map continuous value to 0/1/2 with two thresholds."""
    v = float(value)
    if higher_better:
        if v >= hi:
            return 2
        if v >= mid:
            return 1
        return 0
    if v <= lo:
        return 2
    if v <= mid:
        return 1
    return 0


def compute_single_image_metrics(image_path: str) -> dict[str, float]:
    """Quantifiable single-image stats (rubric observation scale ~1024 long side)."""
    import numpy as np
    from PIL import Image

    im0 = Image.open(image_path).convert("RGB")
    w0, h0 = im0.size
    megapix = (w0 * h0) / 1_000_000.0
    short_side = float(min(w0, h0))
    long_side = float(max(w0, h0))

    # Unified observe size (rubric §0.3)
    scale = min(1.0, 1024.0 / max(long_side, 1.0))
    ow = max(64, int(round(w0 * scale)))
    oh = max(64, int(round(h0 * scale)))
    im = im0.resize((ow, oh), Image.Resampling.LANCZOS)
    a = np.asarray(im).astype("float32") / 255.0
    # Y channel in 0..255 space for clip thresholds
    Y = (0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]) * 255.0
    L = Y / 255.0

    contrast = float(min(1.0, L.std() * 3.0))
    gy = float(np.abs(np.diff(L, axis=0)).mean())
    gx = float(np.abs(np.diff(L, axis=1)).mean())
    edge_energy = float(min(1.0, (gx + gy) * 8.0))

    warm = a[..., 0] - a[..., 2]
    cw = float(min(1.0, abs(warm.mean()) * 4.0 + warm.std() * 2.0))

    blur = L.copy()
    blur[1:-1, 1:-1] = (
        L[:-2, 1:-1] + L[2:, 1:-1] + L[1:-1, :-2] + L[1:-1, 2:]
    ) * 0.25
    hf = float(min(1.0, np.abs(L - blur).mean() * 12.0))
    Lb = blur
    bgy = float(np.abs(np.diff(Lb, axis=0)).mean())
    bgx = float(np.abs(np.diff(Lb, axis=1)).mean())
    structured_edge = float(min(1.0, (bgx + bgy) * 10.0))
    edge_coherence = float(
        _clip(structured_edge / max(edge_energy, 1e-3), 0.0, 1.5) / 1.5
    )
    noise_as_structure = float(_clip(hf * (1.0 - edge_coherence) * 1.4, 0.0, 1.0))

    # Soft-edge / melt proxy: fraction of edge mass that is weak after blur
    gmag = np.zeros_like(L)
    gmag[1:, :] += np.abs(np.diff(L, axis=0))
    gmag[:, 1:] += np.abs(np.diff(L, axis=1))
    edge_mask = gmag > float(np.percentile(gmag, 70))
    soft = float(((gmag < float(np.percentile(gmag, 55))) & edge_mask).mean()) if edge_mask.any() else 0.5
    # melt_ratio ≈ weak structured edges among strong-edge candidates
    melt_ratio = float(_clip(
        0.55 * (1.0 - edge_coherence) + 0.25 * soft + 0.20 * noise_as_structure,
        0.0,
        1.0,
    ))

    side = 256
    im_s = im0.resize((side, side), Image.Resampling.LANCZOS)
    Ls = np.asarray(im_s.convert("L"), dtype="float32")
    lap = (
        -4 * Ls[1:-1, 1:-1]
        + Ls[:-2, 1:-1]
        + Ls[2:, 1:-1]
        + Ls[1:-1, :-2]
        + Ls[1:-1, 2:]
    )
    lap_var = float(lap.var())
    sharpness = float(min(1.0, math.log1p(lap_var) / math.log1p(2500.0)))

    # 256px readability (C6)
    L256 = Ls / 255.0
    e256 = float(min(1.0, (np.abs(np.diff(L256, axis=0)).mean() + np.abs(np.diff(L256, axis=1)).mean()) * 10.0))
    read_256 = float(_clip(0.55 * e256 + 0.45 * sharpness, 0.0, 1.0))

    chroma = np.sqrt((a[..., 0] - L) ** 2 + (a[..., 1] - L) ** 2 + (a[..., 2] - L) ** 2)
    color_rich = float(min(1.0, chroma.std() * 4.0 + chroma.mean() * 2.0))
    cmax = a.max(axis=-1)
    cmin = a.min(axis=-1)
    with np.errstate(invalid="ignore", divide="ignore"):
        sat = np.where(cmax > 1e-6, (cmax - cmin) / np.maximum(cmax, 1e-6), 0.0)
    sat = np.nan_to_num(sat, nan=0.0, posinf=0.0, neginf=0.0)
    sat_mean = float(sat.mean())
    sat_std = float(sat.std())

    mid = float(((L > 0.15) & (L < 0.85)).mean())
    # Rubric L2: dead black Y≤3, overexpose Y≥252
    clip_dead = float((Y <= 3.0).mean())
    clip_blow = float((Y >= 252.0).mean())
    clip_shadow = float((Y <= 10.0).mean())
    clip_highlight = float((Y >= 245.0).mean())
    clip_extreme = float(clip_dead + clip_blow)

    # Lab-ish a*/b* on midtones (L3)
    mid_m = (L > 0.25) & (L < 0.75)
    if mid_m.any():
        # crude opponent: R-G ~ a*, Y-B ~ b*
        a_star = float(np.abs((a[..., 0] - a[..., 1])[mid_m]).mean() * 100.0)
        b_star = float(np.abs((0.5 * (a[..., 0] + a[..., 1]) - a[..., 2])[mid_m]).mean() * 100.0)
        wb_dev = float(max(a_star, b_star))
    else:
        wb_dev = 20.0

    # Center vs surround (subject proxy)
    h, w = L.shape
    cy0, cy1 = int(h * 0.28), int(h * 0.72)
    cx0, cx1 = int(w * 0.28), int(w * 0.72)
    center = L[cy0:cy1, cx0:cx1]
    # surround ring
    mask = np.ones_like(L, dtype=bool)
    mask[cy0:cy1, cx0:cx1] = False
    surround = L[mask]
    center_contrast = float(center.std()) if center.size else 0.0
    surround_contrast = float(surround.std()) if surround.size else 0.0
    subj_bg_contrast_gap = float(
        _clip((center_contrast - surround_contrast) / max(surround_contrast, 0.05), -1.0, 3.0)
    )
    # edge density ratio center/background (T3 / C2)
    g_c = float(np.abs(np.diff(center, axis=0)).mean() + np.abs(np.diff(center, axis=1)).mean()) if center.size > 4 else 0.0
    # build surround as full minus center mean of local diffs — approximate with border bands
    border = np.concatenate([L[: h // 8, :].ravel(), L[-h // 8 :, :].ravel(), L[:, : w // 8].ravel(), L[:, -w // 8 :].ravel()])
    # local edge on border strip via std as proxy
    g_b = float(border.std() * 0.35)
    edge_density_ratio = float(g_c / max(g_b, 1e-4))

    center_mean = float(center.mean()) if center.size else 0.5
    border_mean = float(surround.mean()) if surround.size else 0.5
    center_dominance = float(_clip((center_mean - border_mean) * 2.5 + 0.5, 0.0, 1.0))

    # 3×3 visual weight (C4) — mean |L-0.5| + local edge
    weights_3x3 = []
    for bi in range(3):
        for bj in range(3):
            y0, y1 = bi * h // 3, (bi + 1) * h // 3
            x0, x1 = bj * w // 3, (bj + 1) * w // 3
            cell = L[y0:y1, x0:x1]
            ew = float(np.abs(np.diff(cell, axis=0)).mean() + np.abs(np.diff(cell, axis=1)).mean()) if cell.size > 4 else 0.0
            weights_3x3.append(float(np.abs(cell - 0.5).mean() + ew * 2.0))
    wmax, wmin = max(weights_3x3), max(min(weights_3x3), 1e-6)
    grid_imbalance = float(wmax / wmin)

    # Salience gap proxy (C1): top-2 cell weight gap
    ordered = sorted(weights_3x3, reverse=True)
    sal_gap = float((ordered[0] - ordered[1]) / max(ordered[0], 1e-6)) if len(ordered) >= 2 else 0.0

    # Border crop pressure (C3): mass near edges
    edge_band = max(2, min(h, w) // 20)
    border_mass = float(
        (L[:edge_band, :].mean() + L[-edge_band:, :].mean() + L[:, :edge_band].mean() + L[:, -edge_band:].mean()) / 4.0
    )
    # high border edge energy suggests cut through content
    border_edge = float(
        (
            np.abs(np.diff(L[:edge_band, :], axis=1)).mean()
            + np.abs(np.diff(L[-edge_band:, :], axis=1)).mean()
            + np.abs(np.diff(L[:, :edge_band], axis=0)).mean()
            + np.abs(np.diff(L[:, -edge_band:], axis=0)).mean()
        )
        / 4.0
        * 8.0
    )
    crop_pressure = float(_clip(0.5 * border_mass + 0.5 * min(1.0, border_edge), 0.0, 1.0))

    # Depth cues (C5): sharpness/contrast falloff center→border
    depth_cue = float(_clip((center_contrast - surround_contrast) * 4.0 + (g_c - g_b) * 3.0, 0.0, 1.0))

    # Material differentiation proxy (T1): chroma+hf variance across 4 quadrants
    quads = []
    for qi in range(2):
        for qj in range(2):
            y0, y1 = qi * h // 2, (qi + 1) * h // 2
            x0, x1 = qj * w // 2, (qj + 1) * w // 2
            qc = chroma[y0:y1, x0:x1]
            qh = np.abs((L - blur)[y0:y1, x0:x1])
            quads.append((float(qc.mean()), float(qh.mean())))
    mat_spread = float(
        np.std([q[0] for q in quads]) * 3.0 + np.std([q[1] for q in quads]) * 4.0
    )

    res_score = float(
        min(1.0, max(0.0, (short_side - 256.0) / 768.0) * 0.55 + min(1.0, megapix / 1.2) * 0.45)
    )
    mush = float(
        _clip(
            (1.0 - sharpness) * 0.40
            + (1.0 - edge_coherence) * 0.25
            + (1.0 - res_score) * 0.20
            + noise_as_structure * 0.15,
            0.0,
            1.0,
        )
    )
    clarity = float(
        _clip(
            0.34 * sharpness
            + 0.22 * edge_coherence
            + 0.18 * structured_edge
            + 0.16 * res_score
            + 0.10 * edge_energy
            - 0.25 * noise_as_structure,
            0.0,
            1.0,
        )
    )
    drama = float(_clip(0.40 * contrast + 0.35 * cw + 0.25 * edge_energy, 0.0, 1.0))

    return {
        "width": float(w0),
        "height": float(h0),
        "megapixels": round(megapix, 3),
        "short_side": short_side,
        "long_side": long_side,
        "contrast": round(contrast, 4),
        "edge_energy": round(edge_energy, 4),
        "structured_edge": round(structured_edge, 4),
        "edge_coherence": round(edge_coherence, 4),
        "cold_warm_separation": round(cw, 4),
        "texture_hf": round(hf, 4),
        "sharpness": round(sharpness, 4),
        "laplacian_var": round(lap_var, 2),
        "color_richness": round(color_rich, 4),
        "sat_mean": round(sat_mean, 4),
        "sat_std": round(sat_std, 4),
        "midtone_mass": round(mid, 4),
        "clip_shadow": round(clip_shadow, 4),
        "clip_highlight": round(clip_highlight, 4),
        "clip_dead": round(clip_dead, 4),
        "clip_blow": round(clip_blow, 4),
        "clip_extreme": round(clip_extreme, 4),
        "wb_dev": round(wb_dev, 3),
        "center_dominance": round(center_dominance, 4),
        "subj_bg_contrast_gap": round(subj_bg_contrast_gap, 4),
        "edge_density_ratio": round(edge_density_ratio, 4),
        "grid_imbalance": round(grid_imbalance, 3),
        "salience_gap": round(sal_gap, 4),
        "crop_pressure": round(crop_pressure, 4),
        "depth_cue": round(depth_cue, 4),
        "read_256": round(read_256, 4),
        "melt_ratio": round(melt_ratio, 4),
        "material_spread": round(min(1.0, mat_spread), 4),
        "resolution_score": round(res_score, 4),
        "mushiness": round(mush, 4),
        "noise_as_structure": round(noise_as_structure, 4),
        "clarity": round(clarity, 4),
        "drama": round(drama, 4),
    }


def _diagnostic_vs_ref(gen_path: str, ref_path: str) -> dict[str, float]:
    import numpy as np
    from PIL import Image

    def _load(path: str):
        im = Image.open(path).convert("RGB")
        im = im.resize((384, 384), Image.Resampling.LANCZOS)
        return np.asarray(im).astype("float32") / 255.0

    g = _load(gen_path)
    r = _load(ref_path)
    mse = float(np.mean((g - r) ** 2) * 255.0 ** 2)
    gL = 0.299 * g[..., 0] + 0.587 * g[..., 1] + 0.114 * g[..., 2]
    rL = 0.299 * r[..., 0] + 0.587 * r[..., 1] + 0.114 * r[..., 2]
    mae = float(np.mean(np.abs(gL - rL)))
    struct = float(max(0.0, min(1.0, 1.0 - mae * 2.5)))
    return {"mse": round(mse, 2), "struct": round(struct, 4)}


def _fill_metric_defaults(m: dict[str, float]) -> dict[str, float]:
    """Allow synthetic / partial metrics (dry-run) to drive checklist."""
    out = dict(m)
    out.setdefault("short_side", 1024.0)
    out.setdefault("long_side", 1024.0)
    out.setdefault("edge_coherence", float(out.get("sharpness") or 0.4))
    out.setdefault("structured_edge", float(out.get("edge_energy") or 0.4) * 0.9)
    out.setdefault("noise_as_structure", float(out.get("mushiness") or 0.3) * 0.5)
    out.setdefault("clarity", float(out.get("sharpness") or 0.4))
    out.setdefault("drama", float(out.get("contrast") or 0.4))
    out.setdefault("sat_mean", 0.35)
    out.setdefault("sat_std", 0.12)
    out.setdefault("clip_shadow", 0.05)
    out.setdefault("clip_highlight", 0.02)
    out.setdefault("clip_extreme", float(out.get("clip_shadow") or 0) + float(out.get("clip_highlight") or 0))
    out.setdefault("clip_dead", float(out.get("clip_shadow") or 0) * 0.5)
    out.setdefault("clip_blow", float(out.get("clip_highlight") or 0) * 0.5)
    out.setdefault("wb_dev", 8.0)
    out.setdefault("center_dominance", 0.5)
    out.setdefault("subj_bg_contrast_gap", float(out.get("contrast") or 0.4))
    out.setdefault("edge_density_ratio", 1.0 + float(out.get("edge_energy") or 0.4))
    out.setdefault("grid_imbalance", 1.5 + float(out.get("mushiness") or 0.3) * 2.0)
    out.setdefault("salience_gap", 0.15 + float(out.get("contrast") or 0.3) * 0.3)
    out.setdefault("crop_pressure", 0.35)
    out.setdefault("depth_cue", float(out.get("contrast") or 0.4) * 0.8)
    out.setdefault("read_256", float(out.get("clarity") or out.get("sharpness") or 0.4))
    out.setdefault("melt_ratio", float(out.get("mushiness") or 0.3))
    out.setdefault("material_spread", float(out.get("color_richness") or 0.4) * 0.8)
    out.setdefault("resolution_score", 0.6)
    out.setdefault("midtone_mass", 0.55)
    out.setdefault("cold_warm_separation", float(out.get("contrast") or 0.4) * 0.8)
    out.setdefault("color_richness", 0.4)
    out.setdefault("texture_hf", 0.35)
    out.setdefault(
        "mushiness",
        float(
            _clip(
                (1.0 - float(out.get("sharpness") or 0.4)) * 0.5
                + (1.0 - float(out.get("edge_coherence") or 0.4)) * 0.3
                + float(out.get("noise_as_structure") or 0.2) * 0.2,
                0.0,
                1.0,
            )
        ),
    )
    return out


def _score_items(metrics: dict[str, float], *, has_ref: bool, struct: float | None) -> dict[str, dict[str, int | None]]:
    """Return per-dim item ratings: 0/1/2 or None (uncertain/N/A).

    Audit (gpt-6-sol): weak semantic proxies must NOT cast a hard 0.
    Only score items we can defend with pixel evidence; else None.
    """
    m = _fill_metric_defaults(metrics)

    # --- composition ---
    # C1 subject uniqueness: no segmentation → N/A (never fake 0)
    c1 = None
    # C2 visual hierarchy: center≠subject → N/A
    c2 = None
    # C3 crop pressure (layout / border mass) — measurable
    cp = float(m["crop_pressure"])
    if cp >= 0.78:
        c3 = 0
    elif cp >= 0.52:
        c3 = 1
    else:
        c3 = 2
    # C4 3×3 balance — measurable layout
    imb = float(m["grid_imbalance"])
    if imb > 5.0:
        c4 = 0
    elif imb > 2.5:
        c4 = 1
    else:
        c4 = 2
    # C5 depth: single contrast-falloff cue insufficient → N/A
    c5 = None
    # C6 thumbnail readability — soft; mid defaults to 1 (not 0)
    r256 = float(m["read_256"])
    if r256 < 0.12:
        c6 = 0
    elif r256 < 0.40:
        c6 = 1
    else:
        c6 = 2

    # --- lighting ---
    l1 = None  # light direction — semantic
    ce = float(m["clip_extreme"])
    if ce > 0.08:
        l2 = 0
    elif ce >= 0.025:
        l2 = 1
    else:
        l2 = 2
    # L3 WB: no neutral target → N/A (don't punish warm dusk / cool night)
    l3 = None
    # L4 light-color chaos: only fail on extreme inconsistency
    cw = float(m["cold_warm_separation"])
    sat_std = float(m.get("sat_std") or 0)
    if cw < 0.08 and sat_std > 0.32:
        l4 = 0
    elif cw < 0.18:
        l4 = 1
    else:
        l4 = 2
    # L5 subject contrast: center≠subject → N/A
    l5 = None
    l6 = None

    # --- perspective: offline cannot verify anatomy/vanishing points → all N/A ---
    p1 = p2 = p3 = p4 = p5 = p6 = None

    # --- texture ---
    # T1 materials: quadrant chroma ≠ materials → N/A
    t1 = None
    # T2 structure consistency — weak but pixel-defensible
    t2_sig = float(m["edge_coherence"]) * (1.0 - 0.45 * float(m["mushiness"]))
    if t2_sig < 0.22:
        t2 = 0
    elif t2_sig < 0.48:
        t2 = 1
    else:
        t2 = 2
    # T3 detail hierarchy via center box → N/A
    t3 = None
    # T4 edge melt: mush proxy ≠ melt length ratio → N/A (audit #1)
    t4 = None
    # T5 noise-as-structure — measurable
    nas = float(m["noise_as_structure"])
    if nas > 0.48:
        t5 = 0
    elif nas > 0.22:
        t5 = 1
    else:
        t5 = 2
    # T6 local structure / clarity — measurable tech proxy
    clar = float(m["clarity"])
    if clar < 0.22:
        t6 = 0
    elif clar < 0.48:
        t6 = 1
    else:
        t6 = 2

    # --- spec_style ---
    s1 = s2 = s6 = None
    mush = float(m["mushiness"])
    sat = float(m["sat_mean"])
    if mush > 0.70 and sat > 0.55:
        s3 = 0
    elif mush > 0.48 or float(m["color_richness"]) < 0.15:
        s3 = 1
    else:
        s3 = 2
    if has_ref and struct is not None:
        if struct >= 0.92:
            s4 = 1
        elif struct >= 0.55:
            s4 = 2
        elif struct >= 0.35:
            s4 = 1
        else:
            s4 = 0
    else:
        s4 = None
    # S5 tech resolution: report mildly — never treat tiny as art failure (audit)
    # Keep as tech check but floor at 1 for short_side≥256
    ss = float(m["short_side"])
    if ss < 256:
        s5 = 0
    elif ss < 720:
        s5 = 1
    else:
        s5 = 2

    return {
        "composition": {"C1": c1, "C2": c2, "C3": c3, "C4": c4, "C5": c5, "C6": c6},
        "lighting_color": {"L1": l1, "L2": l2, "L3": l3, "L4": l4, "L5": l5, "L6": l6},
        "perspective_anatomy": {"P1": p1, "P2": p2, "P3": p3, "P4": p4, "P5": p5, "P6": p6},
        "texture_detail": {"T1": t1, "T2": t2, "T3": t3, "T4": t4, "T5": t5, "T6": t6},
        "spec_style": {"S1": s1, "S2": s2, "S3": s3, "S4": s4, "S5": s5, "S6": s6},
    }


def _dim_from_items(
    dim: str, ratings: dict[str, int | None]
) -> tuple[float | None, float, dict[str, Any]]:
    """Compute S and item-weight coverage. Shrink toward NEUTRAL_PRIOR when sparse."""
    specs = _ITEM_WEIGHTS[dim]
    used_w = 0.0
    raw = 0.0
    detail = {}
    for item_id, w in specs:
        r = ratings.get(item_id)
        detail[item_id] = {"w": w, "r": r, "status": "scored" if r is not None else "uncertain_na"}
        if r is None:
            continue
        used_w += w
        raw += w * (float(r) / 2.0)
    min_w = (
        _DIM_MIN_ITEM_WEIGHT_PERSPECTIVE
        if dim == "perspective_anatomy"
        else _DIM_MIN_ITEM_WEIGHT
    )
    if used_w < min_w:
        return None, used_w / 100.0, detail
    P = raw / used_w * 100.0
    S_raw = P / 10.0
    item_cov = used_w / 100.0
    # Mild shrink toward合格 prior for missing items (audit §聚合) —
    # not a full blend, so all-2 measurable items can still reach ~9.
    missing = 1.0 - item_cov
    S = S_raw - missing * (S_raw - NEUTRAL_PRIOR) * 0.45
    return round(S, 2), item_cov, detail


def _apply_hard_caps(
    dims: dict[str, float | None],
    metrics: dict[str, float],
    items: dict[str, dict[str, int | None]],
) -> dict[str, float | None]:
    """Rubric §8 hard caps — only when evidence is real (audit: no short_side / P5 / fake-melt caps)."""
    m = _fill_metric_defaults(metrics)
    out = dict(dims)

    # composition ≤5 only if thumbnail truly unreadable (C6=0)
    c = items.get("composition") or {}
    if out.get("composition") is not None and c.get("C6") == 0:
        out["composition"] = min(float(out["composition"]), 5.0)

    # lighting ≤5 if dead/blow >8% (real histogram evidence)
    if out.get("lighting_color") is not None and float(m.get("clip_extreme") or 0) > 0.08:
        out["lighting_color"] = min(float(out["lighting_color"]), 5.0)

    # Removed: texture short_side / melt_ratio caps; perspective P5-only cap (audit #1)
    return out


def _band_label(s: float) -> float:
    """Nearest rubric band center for meta display."""
    for b in (3.0, 5.0, 7.0, 8.5, 9.5):
        if s < b + (0.0 if b == 9.5 else {3.0: 1.0, 5.0: 1.0, 7.0: 0.75, 8.5: 0.5}[b]):
            if s < 3.0:
                return 3.0
            if s < 5.0:
                return 3.0 if s < 4.0 else 5.0
            if s < 7.0:
                return 5.0 if s < 6.0 else 7.0
            if s < 8.5:
                return 7.0
            if s < 9.5:
                return 8.5
            return 9.5
    return 9.5


def band_of_score(s: float) -> float:
    if s < 3.0:
        return 3.0
    if s < 5.0:
        return 5.0 if s >= 4.0 else 3.0
    if s < 7.0:
        return 7.0 if s >= 6.0 else 5.0
    if s < 8.5:
        return 7.0
    if s < 9.5:
        return 8.5
    return 9.5


def _weights_for(api_scale: str, prompt_mode: str = "") -> dict[str, float]:
    s = (api_scale or "medium").strip().lower()
    mode = (prompt_mode or "").strip().lower()
    if mode == "style_jump" or "bold" in s:
        return dict(_WEIGHTS["recompose"])
    if s not in _WEIGHTS:
        s = "medium"
    return dict(_WEIGHTS[s])


def weighted_score_na(
    dims: dict[str, float | None], weights: dict[str, float]
) -> tuple[float, float]:
    """Total with N/A dims shrunk to NEUTRAL_PRIOR (half weight) — no infinite renormalize.

    Audit: missing dims must not let remaining proxies dominate the total.
    """
    total_w_all = sum(float(weights.get(k, 0.0)) for k in _DIM_KEYS) or 1.0
    measured_w = 0.0
    num = 0.0
    den = 0.0
    for k in _DIM_KEYS:
        w = float(weights.get(k, 0.0))
        if dims.get(k) is None:
            # low-confidence prior — half influence
            num += w * 0.5 * NEUTRAL_PRIOR
            den += w * 0.5
        else:
            num += w * float(dims[k])
            den += w
            measured_w += w
    coverage = measured_w / total_w_all
    score = num / max(den, 1e-6)
    # N/A dims already contribute half-weight prior — no second full shrink
    return round(score, 2), round(coverage, 3)


def weighted_score(dims: dict[str, float], weights: dict[str, float]) -> float:
    """Compat: dims without N/A."""
    total, _ = weighted_score_na({k: dims.get(k) for k in _DIM_KEYS}, weights)
    return total


def score_checklist(
    metrics: dict[str, float],
    *,
    api_scale: str = "medium",
    prompt_mode: str = "",
    has_ref: bool = False,
    struct: float | None = None,
) -> dict[str, Any]:
    """Core: metrics → checklist 0/1/2 → dims → total."""
    items = _score_items(metrics, has_ref=has_ref, struct=struct)
    dims: dict[str, float | None] = {}
    coverage_dim: dict[str, float] = {}
    checklist: dict[str, Any] = {}
    for dim in _DIM_KEYS:
        S, cov, detail = _dim_from_items(dim, items[dim])
        dims[dim] = S
        coverage_dim[dim] = cov
        checklist[dim] = detail

    dims = _apply_hard_caps(dims, metrics, items)
    weights = _weights_for(api_scale, prompt_mode)
    score, coverage = weighted_score_na(dims, weights)
    # Without perspective (usual offline), don't claim near-perfect 9.5 band
    if dims.get("perspective_anatomy") is None:
        score = min(score, 8.85)
    bands = {k: (band_of_score(float(dims[k])) if dims[k] is not None else None) for k in _DIM_KEYS}

    # Defects only from scored 0s — never invent semantic defects for N/A proxies
    defects: list[str] = []
    labels = {
        "C3": "裁切/位置失衡", "C4": "空间平衡差", "C6": "缩小后可读性差",
        "L2": "死黑/过曝失控", "L4": "光色逻辑乱",
        "T2": "纹理结构不一致", "T5": "微细节像噪声", "T6": "局部结构不完整",
        "S3": "风格语言不统一", "S4": "与参考规格偏离", "S5": "技术规格不足",
    }
    for dim, detail in checklist.items():
        for iid, info in detail.items():
            if info.get("r") == 0 and iid in labels:
                defects.append(labels[iid])

    strengths: list[str] = []
    for dim, detail in checklist.items():
        twos = [i for i, info in detail.items() if info.get("r") == 2]
        if len(twos) >= 2:
            strengths.append(f"{dim}多项达标({','.join(twos[:3])})")

    return {
        "score": score,
        "dims": dims,
        "bands": bands,
        "weights": weights,
        "coverage": coverage,
        "coverage_dim": coverage_dim,
        "checklist": checklist,
        "defects": defects,
        "strengths": strengths,
        "rankable": coverage >= _RANK_COVERAGE_FLOOR,
        "neutral_prior": NEUTRAL_PRIOR,
        "audit": AUDIT,
    }


def dims_absolute_5d(metrics: dict[str, float], api_scale: str = "medium") -> dict[str, float]:
    """Compat for dry-run: return numeric dims (+ `_bands`); N/A dims filled conservatively."""
    pack = score_checklist(metrics, api_scale=api_scale)
    dims: dict[str, float] = {}
    bands: dict[str, float] = {}
    for k in _DIM_KEYS:
        v = pack["dims"].get(k)
        if v is None:
            # fill with合格 prior for parsers that require 5 numbers
            dims[k] = NEUTRAL_PRIOR
            bands[k] = 7.0
        else:
            dims[k] = float(v)
            bands[k] = float(pack["bands"].get(k) or band_of_score(float(v)))
    dims["_bands"] = bands  # type: ignore[assignment]
    dims["_coverage"] = pack["coverage"]  # type: ignore[assignment]
    dims["_checklist"] = pack["checklist"]  # type: ignore[assignment]
    return dims


def format_dims_str(dims: dict[str, float | None], *, fill_na: bool = True) -> str:
    """Chinese dims string for parse_5d_dims.

    N/A dims fill with NEUTRAL_PRIOR (7.0), never the mean of other dims —
    otherwise parsers invent a fake high perspective/etc. score.
    """

    def _fmt(v: float | None) -> str:
        if v is None:
            return f"{NEUTRAL_PRIOR:.2f}".rstrip("0").rstrip(".") if fill_na else "N/A"
        return f"{float(v):.2f}".rstrip("0").rstrip(".")

    return (
        f"构图{_fmt(dims.get('composition'))}/光影{_fmt(dims.get('lighting_color'))}/"
        f"透视{_fmt(dims.get('perspective_anatomy'))}/质感{_fmt(dims.get('texture_detail'))}/"
        f"风格{_fmt(dims.get('spec_style'))}"
    )


def absolute_5d(
    image_path: str,
    *,
    api_scale: str = "medium",
    prompt_mode: str = "",
    ref_path: str | None = None,
) -> dict[str, Any]:
    p = Path(image_path)
    if not p.is_file():
        raise FileNotFoundError(image_path)

    metrics = compute_single_image_metrics(str(p))
    vs_ref: dict[str, float] = {}
    struct = None
    if ref_path and Path(ref_path).is_file() and Path(ref_path).resolve() != p.resolve():
        vs_ref = _diagnostic_vs_ref(str(p), str(ref_path))
        struct = float(vs_ref.get("struct") or 0.0)

    pack = score_checklist(
        metrics,
        api_scale=api_scale,
        prompt_mode=prompt_mode,
        has_ref=bool(vs_ref),
        struct=struct,
    )
    dims_na = pack["dims"]
    # Public dims: keep N/A as None in meta; numeric dict for callers that need floats
    dims_num = {
        k: (NEUTRAL_PRIOR if dims_na[k] is None else float(dims_na[k])) for k in _DIM_KEYS
    }
    dims_str = format_dims_str(dims_na)

    meta: dict[str, Any] = {
        "track": "A_absolute_5d_offline_checklist",
        "version": SCORER_VERSION,
        "heuristic_stop": HEURISTIC_STOP_THRESHOLD,
        "legacy_showcase_stop": LEGACY_SHOWCASE_STOP,
        "bands": pack["bands"],
        "coverage": pack["coverage"],
        "coverage_dim": pack["coverage_dim"],
        "rankable": pack["rankable"],
        "checklist": pack["checklist"],
        "dims_na": dims_na,
        "note": (
            f"Offline checklist Absolute-5D ({CONTRACT}); audit-patched ({AUDIT}); "
            f"STOP={HEURISTIC_STOP_THRESHOLD}. Weak proxies → N/A; shrink to prior {NEUTRAL_PRIOR}. "
            "Prefer VLM when configured."
        ),
        "api_scale": api_scale,
        "prompt_mode": prompt_mode,
        "contract": CONTRACT,
        "audit": AUDIT,
        "v2_scripted_note": "旧 V2 showcase 分为 scripted，不可横比",
    }
    if vs_ref:
        meta["vs_ref_diagnostic"] = vs_ref

    return {
        "score": pack["score"],
        "dims": dims_num,
        "dims_na": dims_na,
        "dims_str": dims_str,
        "bands": pack["bands"],
        "weights": pack["weights"],
        "metrics": metrics,
        "checklist": pack["checklist"],
        "coverage": pack["coverage"],
        "defects": "；".join(pack["defects"][:6]),
        "strengths": "；".join(pack["strengths"][:4]),
        "vs_ref": vs_ref,
        "struct": float(vs_ref.get("struct") or 0.0),
        "mse": float(vs_ref.get("mse") or 0.0),
        "struct_weight": 0.0,
        "lifted_by_struct_floor": False,
        "meta": meta,
    }


def intent_check(
    *,
    api_scale: str,
    prompt_mode: str = "",
    bot_score: dict[str, Any] | None = None,
    baseline_score: dict[str, Any] | None = None,
    recompose_dir: str = "",
) -> dict[str, Any]:
    """Diagnostic Intent — metric heuristics only (not semantic)."""
    s = (api_scale or "").strip().lower()
    mode = (prompt_mode or "").strip().lower()
    bot = bot_score or {}
    base = baseline_score or {}
    m = bot.get("metrics") or {}
    vs = bot.get("vs_ref") or {}
    struct = float(vs.get("struct") if vs else bot.get("struct") or 0.0)
    lighting = float((bot.get("dims") or {}).get("lighting_color") or 0.0)
    tex = float((bot.get("dims") or {}).get("texture_detail") or 0.0)
    base_score = float(base.get("score") or 0.0)
    bot_total = float(bot.get("score") or 0.0)
    delta = round(bot_total - base_score, 2) if base else None

    if mode == "style_jump" or "bold" in s:
        if vs:
            ok = struct < 0.55
            reason = f"风格跳变：struct={struct:.2f}" if ok else f"风格跳变不足：struct={struct:.2f}"
        else:
            ok = float(m.get("color_richness") or 0) >= 0.35
            reason = "风格跳变：色度尚可" if ok else "风格跳变：色度偏闷"
        return {"pass": ok, "label": "bold_style_jump", "reason": reason, "delta": delta}

    if s == "recompose":
        target = (recompose_dir or "目标机位").strip()
        if vs:
            ok = struct < 0.72
            reason = (
                f"换机位：struct={struct:.2f}（{target[:28]}）"
                if ok
                else f"机位未变：struct={struct:.2f}"
            )
        else:
            ok = float(m.get("edge_energy") or 0) >= 0.25
            reason = "换机位：边缘能量尚可" if ok else "换机位：构图能量不足"
        return {"pass": ok, "label": "recompose_camera", "reason": reason, "delta": delta}

    if s == "high":
        ok = lighting >= 7.0 and tex >= 6.0 and float(m.get("clarity") or 0) >= 0.35
        reason = f"戏剧光/清晰度：光影={lighting:.2f} 质感={tex:.2f}" if ok else f"戏剧光/清晰度不足：光影={lighting:.2f} 质感={tex:.2f}"
        return {"pass": ok, "label": "high_drama_light", "reason": reason, "delta": delta}

    if s == "medium":
        ok = (float(m.get("contrast") or 0) >= 0.22 or lighting >= 6.5) and tex >= 5.5
        reason = "光雾/介质尚可" if ok else "光雾/介质或清晰度偏弱"
        return {"pass": ok, "label": "medium_atmosphere", "reason": reason, "delta": delta}

    ok = float(m.get("clarity") or 0) >= 0.22 and tex >= 5.0
    reason = "微质感可读" if ok else "微质感偏糊/分辨率不足"
    return {"pass": ok, "label": "low_micro_texture", "reason": reason, "delta": delta}


def rewrite_prompt_from_defects(
    base_prompt: str,
    *,
    defects: list[str],
    intent: dict[str, Any] | None = None,
    api_scale: str = "medium",
    recompose_dir: str = "",
    strategy: str = "tail",
    dims: dict[str, Any] | None = None,
) -> str:
    """
    strategy:
      - ``tail`` (default): legacy append; high still gets volume-light hint (old 32bot scripts).
      - ``by_dim``: no universal volume-light; keep short defect list (skill runner has fuller logic).
    """
    bits = [base_prompt.strip()]
    fix = [d.strip() for d in defects if (d or "").strip()]
    if intent and not intent.get("pass"):
        fix.append(str(intent.get("reason") or "档位意图未完成"))
    s = (api_scale or "").lower()
    strat = (strategy or "tail").lower()
    if s == "recompose" and recompose_dir:
        fix.append(f"强化新机位：{recompose_dir}")
    elif s == "high" and strat == "tail":
        fix.append("只抬这一家已经有的层次，并提高结构化清晰度（勿用噪点冒充细节）")
    if strat == "by_dim":
        by_dim_defects = list(defects or [])
        if intent and not intent.get("pass"):
            by_dim_defects.append(str(intent.get("reason") or "档位意图未完成"))
        try:
            from v8_skill_converge_policy import rewrite_reflow_by_dims
            return rewrite_reflow_by_dims(
                base_prompt,
                defects=by_dim_defects,
                dims=dims,
                api_scale=api_scale,
                recompose_dir=recompose_dir,
                max_fixes=2,
            )
        except Exception:
            fix = [d for d in fix if "体积光" not in d][:2] or ["优先修复结构与边缘完整"]
            bits.append("【回流修正】" + "；".join(fix[:2]))
            return " | ".join(bits)
    if fix:
        bits.append("【回流修正】" + "；".join(fix[:4]))
    return " | ".join(bits)


def score_pair(
    bot_path: str,
    ref_path: str,
    *,
    api_scale: str = "medium",
    prompt_mode: str = "",
    recompose_dir: str = "",
) -> dict[str, Any]:
    baseline = absolute_5d(ref_path, api_scale=api_scale, prompt_mode=prompt_mode)
    bot = absolute_5d(bot_path, api_scale=api_scale, prompt_mode=prompt_mode, ref_path=ref_path)
    delta = round(float(bot["score"]) - float(baseline["score"]), 2)
    intent = intent_check(
        api_scale=api_scale,
        prompt_mode=prompt_mode,
        bot_score=bot,
        baseline_score=baseline,
        recompose_dir=recompose_dir,
    )
    return {
        "score": bot["score"],
        "baseline_score": baseline["score"],
        "delta": delta,
        "intent": intent,
        "bot": bot,
        "baseline": baseline,
        "dims": bot["dims"],
        "dims_str": bot["dims_str"],
        "bands": bot.get("bands"),
        "metrics": bot["metrics"],
        "vs_ref": bot["vs_ref"],
        "struct_weight": 0.0,
        "lifted_by_struct_floor": False,
        "meta": {**bot["meta"], "delta": delta, "intent": intent, "baseline_score": baseline["score"]},
    }


if __name__ == "__main__":
    extremes = {
        "dead_flat": {
            "contrast": 0.05, "edge_energy": 0.05, "cold_warm_separation": 0.05,
            "texture_hf": 0.05, "sharpness": 0.05, "color_richness": 0.05,
            "midtone_mass": 0.2, "resolution_score": 0.05, "mushiness": 0.95,
            "edge_coherence": 0.05, "structured_edge": 0.05, "noise_as_structure": 0.8,
            "sat_mean": 0.1, "sat_std": 0.05, "clip_shadow": 0.4, "clip_highlight": 0.3,
            "clip_extreme": 0.35, "center_dominance": 0.9, "short_side": 200,
            "clarity": 0.05, "drama": 0.05, "salience_gap": 0.05, "read_256": 0.08,
            "melt_ratio": 0.40, "grid_imbalance": 6.0, "edge_density_ratio": 0.7,
            "subj_bg_contrast_gap": 0.05, "depth_cue": 0.05, "material_spread": 0.05,
            "wb_dev": 22.0, "crop_pressure": 0.85,
        },
        "soft_ai": {
            "contrast": 0.28, "edge_energy": 0.25, "cold_warm_separation": 0.20,
            "texture_hf": 0.35, "sharpness": 0.45, "color_richness": 0.30,
            "midtone_mass": 0.55, "resolution_score": 0.22, "mushiness": 0.58,
            "edge_coherence": 0.40, "structured_edge": 0.28, "noise_as_structure": 0.35,
            "sat_mean": 0.28, "sat_std": 0.12, "clip_shadow": 0.08, "clip_highlight": 0.02,
            "clip_extreme": 0.04, "center_dominance": 0.55, "short_side": 405,
            "clarity": 0.32, "drama": 0.28, "salience_gap": 0.18, "read_256": 0.32,
            "melt_ratio": 0.12, "grid_imbalance": 2.4, "edge_density_ratio": 1.15,
            "subj_bg_contrast_gap": 0.12, "depth_cue": 0.22, "material_spread": 0.25,
            "wb_dev": 10.0, "crop_pressure": 0.40,
        },
        "decent": {
            "contrast": 0.45, "edge_energy": 0.45, "cold_warm_separation": 0.45,
            "texture_hf": 0.40, "sharpness": 0.55, "color_richness": 0.45,
            "midtone_mass": 0.55, "resolution_score": 0.65, "mushiness": 0.30,
            "edge_coherence": 0.55, "structured_edge": 0.48, "noise_as_structure": 0.18,
            "sat_mean": 0.32, "sat_std": 0.14, "clip_shadow": 0.03, "clip_highlight": 0.02,
            "clip_extreme": 0.015, "center_dominance": 0.50, "short_side": 1024,
            "clarity": 0.55, "drama": 0.48, "salience_gap": 0.28, "read_256": 0.50,
            "melt_ratio": 0.06, "grid_imbalance": 1.8, "edge_density_ratio": 1.45,
            "subj_bg_contrast_gap": 0.22, "depth_cue": 0.40, "material_spread": 0.40,
            "wb_dev": 7.0, "crop_pressure": 0.32,
        },
        "strong": {
            "contrast": 0.72, "edge_energy": 0.70, "cold_warm_separation": 0.68,
            "texture_hf": 0.55, "sharpness": 0.78, "color_richness": 0.60,
            "midtone_mass": 0.58, "resolution_score": 0.85, "mushiness": 0.18,
            "edge_coherence": 0.72, "structured_edge": 0.68, "noise_as_structure": 0.10,
            "sat_mean": 0.36, "sat_std": 0.15, "clip_shadow": 0.02, "clip_highlight": 0.02,
            "clip_extreme": 0.01, "center_dominance": 0.48, "short_side": 1280,
            "clarity": 0.74, "drama": 0.70, "salience_gap": 0.38, "read_256": 0.70,
            "melt_ratio": 0.03, "grid_imbalance": 1.5, "edge_density_ratio": 1.8,
            "subj_bg_contrast_gap": 0.35, "depth_cue": 0.55, "material_spread": 0.55,
            "wb_dev": 5.0, "crop_pressure": 0.25,
        },
        "near_perfect": {
            "contrast": 0.88, "edge_energy": 0.85, "cold_warm_separation": 0.82,
            "texture_hf": 0.70, "sharpness": 0.90, "color_richness": 0.72,
            "midtone_mass": 0.60, "resolution_score": 0.95, "mushiness": 0.10,
            "edge_coherence": 0.88, "structured_edge": 0.85, "noise_as_structure": 0.05,
            "sat_mean": 0.34, "sat_std": 0.14, "clip_shadow": 0.01, "clip_highlight": 0.01,
            "clip_extreme": 0.005, "center_dominance": 0.45, "short_side": 1536,
            "clarity": 0.88, "drama": 0.85, "salience_gap": 0.45, "read_256": 0.85,
            "melt_ratio": 0.02, "grid_imbalance": 1.3, "edge_density_ratio": 2.1,
            "subj_bg_contrast_gap": 0.45, "depth_cue": 0.70, "material_spread": 0.70,
            "wb_dev": 4.0, "crop_pressure": 0.18,
        },
    }
    print(f"=== {SCORER_VERSION} synthetic (medium) STOP={HEURISTIC_STOP_THRESHOLD} ===")
    scores = {}
    for name, m in extremes.items():
        pack = score_checklist(m, api_scale="medium")
        scores[name] = pack["score"]
        print(
            f"  {name:14s} {pack['score']:5.2f}  cov={pack['coverage']:.2f}  "
            f"dims={ {k: pack['dims'][k] for k in _DIM_KEYS} } tex={pack['dims']['texture_detail']}"
        )

    assert scores["dead_flat"] <= 6.0, scores["dead_flat"]
    assert 5.5 <= scores["soft_ai"] <= 8.2, scores["soft_ai"]
    assert 6.5 <= scores["decent"] <= 9.0, scores["decent"]
    assert scores["strong"] >= 7.8, scores["strong"]
    assert scores["near_perfect"] >= HEURISTIC_STOP_THRESHOLD - 0.35, scores["near_perfect"]
    assert scores["near_perfect"] + 0.05 >= scores["strong"]

    ref = Path(__file__).resolve().parent.parent / "comparison/style_refs/style_ref_01_night_city.png"
    if ref.is_file():
        b = absolute_5d(str(ref), api_scale="medium")
        print(
            "night_city ref:", b["score"], "cov", b["coverage"],
            "tex", b["dims_na"]["texture_detail"], "dims", b["dims_str"],
            "defects", b.get("defects"),
        )
        # gpt-6-sol visual ≈7.0 — offline should land near合格, not ~5
        assert 6.2 <= b["score"] <= 8.3, b["score"]
    print(f"absolute_5d_scorer {SCORER_VERSION} OK")
