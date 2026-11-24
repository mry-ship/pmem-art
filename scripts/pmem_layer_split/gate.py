# -*- coding: utf-8 -*-
"""Auto gate: mark ok / dirty from compose metrics + sprite alpha stats + crop feature lock."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image

from .compose import resolve_sprite, trim_alpha
from .defaults import GATE
from .job import Job, load_json


def _asp_err(box_asp: float, spr_asp: float) -> float:
    if box_asp <= 0 or spr_asp <= 0:
        return 99.0
    return abs(math.log(spr_asp / box_asp))


def _alpha_mean(path: Path) -> float:
    im = trim_alpha(Image.open(path).convert("RGBA"))
    a = np.array(im.getchannel("A"), dtype=np.float32) / 255.0
    return float(a.mean()) if a.size else 0.0


def _inner_gaps(path: Path) -> tuple[float, float, float, float]:
    """Transparent gap on each side of the alpha bbox, as a fraction of the frame.

    Returns (top, bottom, left, right). Both ends of one axis large means the
    subject was shrunk into the middle. One large end is a removed neighbor.
    """
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    if w < 2 or h < 2:
        return (1.0, 1.0, 1.0, 1.0)
    mask = im.getchannel("A").point(lambda p: 255 if p > 40 else 0)
    bb = mask.getbbox()
    if not bb:
        return (1.0, 1.0, 1.0, 1.0)
    x0, y0, x1, y1 = bb
    return (y0 / h, (h - y1) / h, x0 / w, (w - x1) / w)


def _content_cut_ratio(path: Path, border: int | None = None) -> float:
    """Fraction of a content-bbox side that is flush with that side.

    Measures the opaque silhouette, not the file border. Letterbox padding
    moves a sliced pond off the file edge, so edge_clip stays near 0 while
    half the content height is a straight cut.
    """
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im.getchannel("A"))
    mask = a > 40
    ys, xs = np.where(mask)
    if len(xs) < 32:
        return 0.0
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    bh = y1 - y0 + 1
    bw = x1 - x0 + 1
    if bh < 8 or bw < 8:
        return 0.0
    b = max(1, int(border if border is not None else GATE.get("content_cut_border_px", 3)))
    b = min(b, bh, bw)
    left = float(mask[y0 : y1 + 1, x0 : x0 + b].any(axis=1).mean())
    right = float(mask[y0 : y1 + 1, x1 - b + 1 : x1 + 1].any(axis=1).mean())
    top = float(mask[y0 : y0 + b, x0 : x1 + 1].any(axis=0).mean())
    bottom = float(mask[y1 - b + 1 : y1 + 1, x0 : x1 + 1].any(axis=0).mean())
    return max(left, right, top, bottom)


def _side_flush_rows(path: Path, border: int | None = None) -> tuple[int, int]:
    """How many rows of the content box touch its left edge, and its right edge.

    A sliced cap is a long run of rows and only a small fraction of a tall box.
    The ratio gate misses that. Top and bottom are not counted: a ground contact
    is a long horizontal edge on purpose.
    """
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im.getchannel("A"))
    mask = a > 40
    ys, xs = np.where(mask)
    if len(xs) < 32:
        return (0, 0)
    x0, y0, x1, y1 = int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
    bh = y1 - y0 + 1
    bw = x1 - x0 + 1
    if bh < 8 or bw < 8:
        return (0, 0)
    b = max(1, int(border if border is not None else GATE.get("content_cut_border_px", 3)))
    b = min(b, bh, bw)
    left = int(mask[y0 : y1 + 1, x0 : x0 + b].any(axis=1).sum())
    right = int(mask[y0 : y1 + 1, x1 - b + 1 : x1 + 1].any(axis=1).sum())
    return left, right


def _edge_clip_ratio(path: Path, border: int | None = None) -> float:
    """Fraction of opaque alpha mass on the outer border (pre-trim).

    High value ⇒ subject likely clipped incomplete at the frame edge
    (spear tip / flame / cloak hem cut off). viking_camp reverse: tent/rack.
    """
    im = Image.open(path).convert("RGBA")
    a = np.asarray(im.getchannel("A"), dtype=np.float32)
    if a.size == 0:
        return 0.0
    mask = a > 40.0
    total = float(mask.sum())
    if total < 32:
        return 0.0
    b = max(1, int(border if border is not None else GATE.get("edge_clip_border_px", 2)))
    h, w = mask.shape
    edge = np.zeros_like(mask, dtype=bool)
    edge[:b, :] = True
    edge[-b:, :] = True
    edge[:, :b] = True
    edge[:, -b:] = True
    return float((mask & edge).sum()) / total


def _bg_bake_score(job: Job, truth: dict) -> float:
    """Max residual bake of bg vs ref inside prop footprints.

    Raw NCC alone false-positives when footprints also cover shared landscape
    (sky / distant trees that correctly remain on the empty stage). Combine with
    MAE: props-still-baked ⇒ low MAE + high NCC; props-removed ⇒ higher MAE.
    bake = ncc_score * clip(1 - mae/0.18, 0, 1). High ⇒ dirty empty stage.
    """
    bg_layer = next((L for L in truth["layers"] if L.get("id") == "bg"), None)
    if bg_layer is None:
        return 0.0
    src = resolve_sprite(job, bg_layer)
    if src is None or not src.exists():
        return 0.0
    try:
        ref = job.open_ref({"ref": truth.get("ref")}).convert("RGB")
    except Exception:
        return 0.0
    bg = Image.open(src).convert("RGB").resize(ref.size, Image.Resampling.LANCZOS)
    ref_a = np.asarray(ref, dtype=np.float32)
    bg_a = np.asarray(bg, dtype=np.float32)
    W, H = ref.size
    scores = []
    for layer in truth["layers"]:
        if layer.get("id") == "bg":
            continue
        px = layer.get("px")
        if not px or len(px) != 4:
            continue
        x0, y0, x1, y1 = [int(v) for v in px]
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(W, x1), min(H, y1)
        if x1 - x0 < 8 or y1 - y0 < 8:
            continue
        a = ref_a[y0:y1, x0:x1].reshape(-1, 3)
        b = bg_a[y0:y1, x0:x1].reshape(-1, 3)
        mae = float(np.mean(np.abs(a - b)) / 255.0)
        a0 = a - a.mean(0)
        b0 = b - b.mean(0)
        denom = float(np.linalg.norm(a0) * np.linalg.norm(b0))
        if denom < 1e-6:
            continue
        ncc = float((a0 * b0).sum() / denom)
        ncc_score = max(0.0, min(1.0, (ncc + 1.0) * 0.5))
        # mae≥0.18 ⇒ sufficiently different (props gone / hole filled)
        mae_w = max(0.0, min(1.0, 1.0 - (mae / 0.18)))
        scores.append(ncc_score * mae_w)
    return float(max(scores)) if scores else 0.0


def _feat_match(sprite: Path, crop: Path) -> float:
    """Masked color+luma agreement after contain-fitting sprite onto the crop box.

    Compares ONLY under the sprite alpha mask so busy crop neighbors / black
    isolation plate do not dominate. Catches total redesigns; allows isolation
    variance. Returns 0..1-ish score (higher = closer to crop truth).
    """
    if not sprite.exists() or not crop.exists():
        return 0.0
    # Compare frames, not a trimmed-and-recentered subject. A tree shoved
    # to the middle of its canvas must not score as if it still spanned the crop.
    spr = Image.open(sprite).convert("RGBA")
    crop_im = Image.open(crop).convert("RGB")
    cw, ch = crop_im.size
    if cw < 8 or ch < 8 or spr.size[0] < 4 or spr.size[1] < 4:
        return 0.0
    sw, sh = spr.size
    scale = min(cw / sw, ch / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    _lanczos = getattr(getattr(Image, "Resampling", Image), "LANCZOS", Image.BICUBIC)
    spr_r = spr.resize((nw, nh), _lanczos)
    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    x0 = (cw - nw) // 2
    y0 = (ch - nh) // 2
    canvas.paste(spr_r, (x0, y0), spr_r.split()[-1])
    arr = np.asarray(canvas)
    crop_a = np.asarray(crop_im).astype(np.float32)
    alpha = arr[:, :, 3].astype(np.float32)
    mask = alpha > 40.0
    if int(mask.sum()) < 32:
        return 0.0
    spr_rgb = arr[:, :, :3].astype(np.float32)[mask]
    crop_rgb = crop_a[mask]
    # mean absolute error in 0..1 → agreement
    mae = float(np.mean(np.abs(spr_rgb - crop_rgb)) / 255.0)
    mae_score = float(np.clip(1.0 - mae * 1.35, 0.0, 1.0))
    # luma NCC under mask
    spr_l = spr_rgb.mean(axis=1)
    crop_l = crop_rgb.mean(axis=1)
    spr_l = spr_l - spr_l.mean()
    crop_l = crop_l - crop_l.mean()
    denom = float(np.linalg.norm(spr_l) * np.linalg.norm(crop_l))
    ncc = float((spr_l * crop_l).sum() / denom) if denom > 1e-6 else 0.0
    ncc_score = float(np.clip((ncc + 1.0) * 0.5, 0.0, 1.0))
    # crude hue-ish hist correlation (R vs G vs B means)
    def _hist3(x: np.ndarray) -> np.ndarray:
        h = []
        for c in range(3):
            hist, _ = np.histogram(x[:, c], bins=16, range=(0, 255), density=True)
            h.append(hist.astype(np.float32))
        return np.concatenate(h)

    hs, hc = _hist3(spr_rgb), _hist3(crop_rgb)
    hs = hs - hs.mean()
    hc = hc - hc.mean()
    hd = float(np.linalg.norm(hs) * np.linalg.norm(hc))
    hist_ncc = float((hs * hc).sum() / hd) if hd > 1e-6 else 0.0
    hist_score = float(np.clip((hist_ncc + 1.0) * 0.5, 0.0, 1.0))
    return float(0.45 * mae_score + 0.35 * ncc_score + 0.20 * hist_score)


def run_gate(job: Job, *, force_ids: list[str] | None = None) -> dict:
    truth = job.load_truth()
    metrics_path = job.root / "_compose_metrics.json"
    if not metrics_path.exists():
        raise FileNotFoundError("run compose first (_compose_metrics.json missing)")
    metrics = load_json(metrics_path)
    status = job.load_status()
    layers_st = status.setdefault("layers", {})
    force = set(force_ids or [])

    dirty = []
    ok = []
    for layer in truth["layers"]:
        lid = layer["id"]
        prev = layers_st.get(lid, {})
        # local bg already ok unless forced
        if prev.get("source") == "local_dig" and lid not in force and prev.get("status") == "ok":
            ok.append(lid)
            continue

        m = metrics.get(lid) or {}
        reasons = []
        if m.get("missing"):
            reasons.append("missing_sprite")
        else:
            asp = _asp_err(float(m.get("box_px_asp") or 1), float(m.get("spr_asp") or 1))
            fill = float(m.get("fill") or 0)
            # autofit size-lock shrinks placed area on purpose — judge fill vs adjusted floor
            scale_mul = float(m.get("scale_mul") or 1.0)
            scale_mul = max(0.5, min(1.0, scale_mul))
            fill_min = GATE["fill_min"] * (scale_mul ** 2)
            fill_max = GATE["fill_max"]
            src = resolve_sprite(job, layer)
            if lid == "bg":
                stretch = float(m.get("stretch_err") or 0)
                if stretch > float(GATE.get("bg_stretch_err_max", 0.12)):
                    reasons.append(
                        f"bg_stretch_err={stretch:.3f}>{GATE['bg_stretch_err_max']} "
                        "(run post_isolate normalize — engine aspect not cropped to canvas)"
                    )
                bake = _bg_bake_score(job, truth)
                m["bg_bake"] = round(bake, 4)
                if bake > float(GATE.get("bg_bake_max", 0.58)):
                    reasons.append(
                        f"bg_bake={bake:.3f}>{GATE['bg_bake_max']} "
                        "(props/character/shadow stains still baked into empty stage — re-isolate bg)"
                    )
            else:
                if asp > GATE["asp_err_max"]:
                    reasons.append(f"asp_err={asp:.3f}>{GATE['asp_err_max']}")
                if fill < fill_min:
                    reasons.append(
                        f"fill={fill:.3f}<{fill_min:.3f}"
                        + (f"(adj×scale_mul={scale_mul:.2f})" if scale_mul < 0.999 else "")
                    )
                if fill > fill_max:
                    reasons.append(f"fill={fill:.3f}>{fill_max}")
                # Slight size is not a redraw. A low scale_mul only means the sprite
                # sits small in the footprint. Redraw is for a different silhouette,
                # missing parts, clipped edges, or baked neighbors. Never widen the
                # box just to raise fill.
                scale_mul_min = float(GATE.get("scale_mul_min", 0.75))
                if scale_mul < scale_mul_min:
                    print(
                        f"NOTE {lid}: scale_mul={scale_mul:.3f}<{scale_mul_min} "
                        "(same object, size only — do not redraw for scale)"
                    )
                if src:
                    am = _alpha_mean(src)
                    if am < GATE["alpha_mean_min"]:
                        reasons.append(f"alpha_mean={am:.3f}<{GATE['alpha_mean_min']}")
                    if am > GATE["alpha_mean_max"]:
                        reasons.append(f"alpha_mean={am:.3f}>{GATE['alpha_mean_max']} (possible tile bleed)")
                    clip = _edge_clip_ratio(src)
                    m["edge_clip"] = round(clip, 4)
                    if clip > GATE["edge_clip_max"]:
                        reasons.append(
                            f"edge_clip={clip:.3f}>{GATE['edge_clip_max']} "
                            "(incomplete — subject touches frame border)"
                        )
                    cut = _content_cut_ratio(src)
                    m["content_cut"] = round(cut, 4)
                    cut_max = float(GATE.get("content_cut_max", 0.18))
                    if cut > cut_max:
                        reasons.append(
                            f"content_cut={cut:.3f}>{cut_max:.2f} "
                            "(straight cut through the subject silhouette)"
                        )
                    left_rows, right_rows = _side_flush_rows(src)
                    m["side_cut_px"] = [left_rows, right_rows]
                    side_max = int(GATE.get("side_cut_px", 120))
                    if left_rows > side_max or right_rows > side_max:
                        reasons.append(
                            f"side_cut_px L{left_rows}/R{right_rows}>{side_max} "
                            "(rounded part sliced on the left or right)"
                        )
                    crop = job.root / "_crops" / f"{lid}.png"
                    if crop.exists():
                        fm = _feat_match(src, crop)
                        m["feat_match"] = round(fm, 4)
                        if fm < GATE["feat_match_min"]:
                            reasons.append(
                                f"feat_match={fm:.3f}<{GATE['feat_match_min']} (crop truth drift)"
                            )
                    top, bot, left, right = _inner_gaps(src)
                    m["inner_gap"] = [round(v, 4) for v in (top, bot, left, right)]
                    gap_max = float(GATE.get("inner_gap_max", 0.14))
                    if top > gap_max and bot > gap_max:
                        reasons.append(
                            f"inner_gap vertical {top:.2f}/{bot:.2f}>{gap_max:.2f} "
                            "(subject shrunk inside the picture band)"
                        )
                    if left > gap_max and right > gap_max:
                        reasons.append(
                            f"inner_gap horizontal {left:.2f}/{right:.2f}>{gap_max:.2f} "
                            "(subject shrunk inside the picture band)"
                        )
                    fit_path = job.root / "_engine_fit.json"
                    if fit_path.is_file():
                        try:
                            fit = load_json(fit_path)
                        except Exception:
                            fit = {}
                        if (fit.get(lid) or {}).get("bled"):
                            reasons.append(
                                "engine_band_bleed (subject drawn into the engine pad bars)"
                            )
            m["asp_err"] = round(asp, 4)

        retries = int(prev.get("retries") or 0)
        if lid in force:
            reasons.append("forced")

        if reasons:
            if retries >= GATE["max_retries"] and "forced" not in reasons:
                st = {
                    "status": "needs_human",
                    "reasons": reasons,
                    "retries": retries,
                    "metrics": m,
                    "file": prev.get("file"),
                }
            else:
                st = {
                    "status": "dirty",
                    "reasons": reasons,
                    "retries": retries,
                    "metrics": m,
                    "file": prev.get("file"),
                    "hint_size": layer.get("size"),
                    "hint_quality": layer.get("quality"),
                }
                dirty.append(lid)
            layers_st[lid] = st
            print(f"GATE {lid}: {st['status']} — {', '.join(reasons)}")
        else:
            src = resolve_sprite(job, layer)
            layers_st[lid] = {
                "status": "ok",
                "reasons": [],
                "retries": retries,
                "metrics": m,
                "file": f"new/{src.name}" if src else prev.get("file"),
                "source": prev.get("source", "isolate"),
            }
            ok.append(lid)
            print(f"GATE {lid}: ok")

    status["dirty_ids"] = dirty
    status["ok_ids"] = ok
    job.save_status(status)
    print(f"gate done: ok={len(ok)} dirty={len(dirty)}")
    return status
