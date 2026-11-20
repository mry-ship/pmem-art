# -*- coding: utf-8 -*-
"""Export crops + template-match footprints back onto the ref."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .compose import cover_resize
from .defaults import (
    CROP_PAD_EDGE_GROW,
    CROP_PAD_EDGE_GROW_MAX,
    CROP_PAD_ISOLATE_EXTRA,
    CROP_PAD_PLAN,
    CROP_PAD_TIGHTEN,
    GATE,
    ISOLATE_USE_CONTEXT_PAD,
)
from .job import (
    Job,
    modules_of,
    pixel_aspect,
    quality_for_area,
    size_for_pixel_aspect,
    assert_allowed_size,
)


def _write_context_pad(
    ref: Image.Image,
    box_xyxy: tuple[int, int, int, int],
    out: Path,
    *,
    label: str,
) -> None:
    """Full-scene pad: dim outside this slot, thick highlight — second isolate reference."""
    x0, y0, x1, y1 = box_xyxy
    base = ref.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 140))
    clear = Image.new("RGBA", (max(1, x1 - x0), max(1, y1 - y0)), (0, 0, 0, 0))
    overlay.paste(clear, (x0, y0))
    vis = Image.alpha_composite(base, overlay).convert("RGB")
    d = ImageDraw.Draw(vis)
    w = max(4, min(base.size) // 120)
    d.rectangle([x0, y0, max(x0 + 1, x1 - 1), max(y0 + 1, y1 - 1)], outline=(0, 255, 220), width=w)
    d.text((x0 + 4, max(0, y0 - 14)), f"EXTRACT: {label}", fill=(255, 240, 0))
    out.parent.mkdir(parents=True, exist_ok=True)
    vis.save(out)


def _parse_grounded(v) -> bool:
    """Accept true/false, 1/0, yes/no — string 'false' must not become True."""
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v).strip().lower()
    if s in ("0", "false", "no", "off", "flying", "suspend", "悬空"):
        return False
    if s in ("1", "true", "yes", "on", "grounded"):
        return True
    raise ValueError(f"grounded={v!r} must be true/false")


def _norm_box_from_plan(m: dict) -> tuple[float, float, float, float]:
    if "crop" in m:
        L, T, BW, BH = m["crop"]
        return float(L), float(T), float(BW), float(BH)
    # truth-style
    return float(m["left"]), float(m["top"]), float(m["width"]), float(m["height"])


def _clamp_box(L: float, T: float, BW: float, BH: float) -> tuple[float, float, float, float]:
    L = max(0.0, min(1.0, L))
    T = max(0.0, min(1.0, T))
    BW = max(0.01, min(1.0 - L, BW))
    BH = max(0.01, min(1.0 - T, BH))
    return L, T, BW, BH


def _sides_content_on_border(
    tile_rgb: np.ndarray,
    *,
    band: int = 3,
    thr: float = 22.0,
    frac: float = 0.12,
) -> set[str]:
    """Which sides of a crop tile look like subject is stuck to the border (clipped)."""
    h, w = tile_rgb.shape[:2]
    if h < 16 or w < 16:
        return set()
    band = max(1, min(band, h // 8, w // 8))
    # Interior reference: avoid edges
    core = tile_rgb[band : h - band, band : w - band]
    if core.size == 0:
        return set()
    # High-frequency / non-flat edge vs smoothed core mean → subject touching frame
    core_mean = core.astype(np.float32).mean(axis=(0, 1))
    touching: set[str] = set()
    strips = {
        "L": tile_rgb[:, :band, :],
        "R": tile_rgb[:, w - band :, :],
        "T": tile_rgb[:band, :, :],
        "B": tile_rgb[h - band :, :, :],
    }
    for side, strip in strips.items():
        dist = np.linalg.norm(strip.astype(np.float32) - core_mean, axis=2)
        # Also catch thin tips: edge strip variance high vs nearly-flat margin
        if float((dist >= thr).mean()) >= frac or float(dist.std()) >= thr * 0.55:
            touching.add(side)
    return touching


def _grow_box_off_edges(
    ref_rgb: np.ndarray,
    L: float,
    T: float,
    BW: float,
    BH: float,
    *,
    grow: float = CROP_PAD_EDGE_GROW,
    max_grow: float = CROP_PAD_EDGE_GROW_MAX,
    max_area_mul: float = 2.4,
) -> tuple[float, float, float, float]:
    """Expand norm box while subject is glued to a crop border.

    Caps total growth and area so busy game art does not balloon to full-frame.
    """
    H, W = ref_rgb.shape[:2]
    grown = 0.0
    base_area = max(1e-6, BW * BH)
    while grown < max_grow - 1e-9:
        if (BW * BH) > base_area * max_area_mul:
            break
        x0, y0 = int(L * W), int(T * H)
        x1, y1 = int((L + BW) * W), int((T + BH) * H)
        x1, y1 = max(x0 + 2, x1), max(y0 + 2, y1)
        tile = ref_rgb[y0:y1, x0:x1]
        sides = _sides_content_on_border(tile, thr=28.0, frac=0.18)
        if not sides:
            break
        step = min(grow, max_grow - grown)
        if "L" in sides:
            L -= step
            BW += step
        if "R" in sides:
            BW += step
        if "T" in sides:
            T -= step
            BH += step
        if "B" in sides:
            BH += step
        L, T, BW, BH = _clamp_box(L, T, BW, BH)
        grown += step
    return L, T, BW, BH


def template_match_box(
    ref_rgb: np.ndarray,
    crop_rgb: np.ndarray,
    hint: tuple[int, int, int, int] | None,
    search_pad: float = 0.12,
) -> tuple[tuple[int, int, int, int], float]:
    """Return (x0,y0,x1,y1), score. Searches near hint if provided."""
    H, W = ref_rgb.shape[:2]
    th, tw = crop_rgb.shape[:2]
    if th >= H or tw >= W:
        # full-frame / oversized → trust hint or full
        if hint:
            return hint, 1.0
        return (0, 0, W, H), 1.0

    gray_ref = cv2.cvtColor(ref_rgb, cv2.COLOR_RGB2GRAY)
    gray_tpl = cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2GRAY)

    if hint is not None:
        hx0, hy0, hx1, hy1 = hint
        pad_x = int((hx1 - hx0) * search_pad) + 8
        pad_y = int((hy1 - hy0) * search_pad) + 8
        sx0 = max(0, hx0 - pad_x)
        sy0 = max(0, hy0 - pad_y)
        sx1 = min(W, hx1 + pad_x)
        sy1 = min(H, hy1 + pad_y)
        # search window must fit template
        if sx1 - sx0 <= tw or sy1 - sy0 <= th:
            sx0, sy0, sx1, sy1 = 0, 0, W, H
        region = gray_ref[sy0:sy1, sx0:sx1]
        if region.shape[0] <= th or region.shape[1] <= tw:
            region = gray_ref
            sx0, sy0 = 0, 0
        res = cv2.matchTemplate(region, gray_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        x0 = sx0 + max_loc[0]
        y0 = sy0 + max_loc[1]
    else:
        res = cv2.matchTemplate(gray_ref, gray_tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        x0, y0 = max_loc

    x1, y1 = x0 + tw, y0 + th
    return (x0, y0, min(W, x1), min(H, y1)), float(max_val)


def setup_and_calibrate(
    job: Job,
    *,
    skip_match: bool = False,
    tighten_from_bg: bool = True,
) -> dict:
    plan = job.load_plan()
    ref = job.open_ref(plan)
    W, H = ref.size
    ref_rgb = np.array(ref.convert("RGB"))
    job.crops_dir.mkdir(exist_ok=True)

    # Optional: empty-stage bg plate → subject mask → shrink boxes to real size
    from .footprint import (
        crop_content_norm_box,
        diff_subject_mask,
        expand_norm_box,
        map_crop_content_to_full,
        resolve_bg_plate,
        tighten_norm_box_with_mask,
        write_footprints,
    )

    subj_mask = None
    bg_mask_ok = False
    bg_path = resolve_bg_plate(job) if tighten_from_bg else None
    if not tighten_from_bg:
        print("tighten-from-bg: disabled")
    if bg_path is not None:
        # Same aspect contract as compose: never non-uniform stretch the bg plate.
        bg_fit = cover_resize(Image.open(bg_path).convert("RGBA"), W, H).convert("RGB")
        bg_rgb = np.array(bg_fit)
        subj_mask = diff_subject_mask(ref_rgb, bg_rgb)
        mf = float(subj_mask.mean())
        # Empty stage should leave most pixels similar; if almost everything
        # differs, bg plate is wrong / furnished — fall back to per-crop trim.
        bg_mask_ok = 0.05 <= mf <= 0.55
        print(f"tighten-from-bg: {bg_path.name} mask_frac={mf:.3f} usable={bg_mask_ok}")

    guide = ref.copy()
    draw = ImageDraw.Draw(guide)
    layers = []
    min_score = GATE["match_score_min"]

    for m in modules_of(plan):
        L, T, BW, BH = _clamp_box(*_norm_box_from_plan(m))
        # Fixed generous pad only. Iterative edge-grow on busy game art balloons to
        # full-frame; Agent/plan + CROP_PAD_PLAN / ISOLATE_EXTRA carry the margin.
        if m.get("id") != "bg" and m.get("mode") != "full" and not (BW >= 0.98 and BH >= 0.98):
            L, T, BW, BH = expand_norm_box(L, T, BW, BH, pad=CROP_PAD_PLAN)
            L, T, BW, BH = _clamp_box(L, T, BW, BH)
        x0, y0 = int(L * W), int(T * H)
        x1, y1 = int((L + BW) * W), int((T + BH) * H)
        x1, y1 = max(x0 + 1, x1), max(y0 + 1, y1)
        crop = ref.crop((x0, y0, x1, y1))
        crop_path = job.crops_dir / f"{m['id']}.png"
        crop.save(crop_path)

        score = 1.0
        cal_fail = False
        if skip_match or m.get("id") == "bg" or m.get("mode") == "full" or (BW >= 0.98 and BH >= 0.98):
            if m.get("id") == "bg" or m.get("mode") == "full" or (BW >= 0.98 and BH >= 0.98):
                mx0, my0, mx1, my1 = 0, 0, W, H
            else:
                mx0, my0, mx1, my1 = x0, y0, x1, y1
        else:
            (mx0, my0, mx1, my1), score = template_match_box(
                ref_rgb, np.array(crop.convert("RGB")), (x0, y0, x1, y1)
            )
            if score < min_score:
                cal_fail = True
                mx0, my0, mx1, my1 = x0, y0, x1, y1

        L2, T2 = mx0 / W, my0 / H
        BW2, BH2 = (mx1 - mx0) / W, (my1 - my0) / H
        L2, T2, BW2, BH2 = _clamp_box(L2, T2, BW2, BH2)

        # Lock size: prefer bg-diff silhouette; else trim content inside crop tile
        if (
            m.get("id") != "bg"
            and m.get("mode") != "full"
            and not (BW2 >= 0.98 and BH2 >= 0.98)
        ):
            if bg_mask_ok and subj_mask is not None:
                L2, T2, BW2, BH2 = tighten_norm_box_with_mask(
                    subj_mask, L2, T2, BW2, BH2, pad=CROP_PAD_TIGHTEN
                )
            else:
                # re-load crop for this matched box
                _c = ref.crop(
                    (
                        int(L2 * W),
                        int(T2 * H),
                        max(int(L2 * W) + 1, int((L2 + BW2) * W)),
                        max(int(T2 * H) + 1, int((T2 + BH2) * H)),
                    )
                )
                content = crop_content_norm_box(
                    np.array(_c.convert("RGB")),
                    pad_px=max(4, int(0.03 * min(_c.size))),
                )
                if content is not None:
                    L2, T2, BW2, BH2 = map_crop_content_to_full(L2, T2, BW2, BH2, content)
            L2, T2, BW2, BH2 = _clamp_box(L2, T2, BW2, BH2)

        # Footprint / compose box (truth) — keep the padded plan/silhouette box
        truth_L, truth_T, truth_W, truth_H = L2, T2, BW2, BH2
        # Isolate crop PNG — fixed extra margin only (no second edge-grow into neighbors)
        if m.get("id") != "bg" and m.get("mode") != "full" and not (
            BW2 >= 0.98 and BH2 >= 0.98
        ):
            iso_L, iso_T, iso_W, iso_H = expand_norm_box(
                L2, T2, BW2, BH2, pad=CROP_PAD_ISOLATE_EXTRA
            )
            iso_L, iso_T, iso_W, iso_H = _clamp_box(iso_L, iso_T, iso_W, iso_H)
        else:
            iso_L, iso_T, iso_W, iso_H = truth_L, truth_T, truth_W, truth_H

        # refresh crop from GENEROUS isolate box (what the model sees)
        cx0, cy0 = int(iso_L * W), int(iso_T * H)
        cx1, cy1 = int((iso_L + iso_W) * W), int((iso_T + iso_H) * H)
        crop2 = ref.crop((cx0, cy0, max(cx0 + 1, cx1), max(cy0 + 1, cy1)))
        crop2.save(crop_path)

        # Full-scene context pad: this slot highlighted, outside dimmed
        if (
            ISOLATE_USE_CONTEXT_PAD
            and m.get("id") != "bg"
            and m.get("mode") != "full"
            and not (iso_W >= 0.98 and iso_H >= 0.98)
        ):
            _write_context_pad(
                ref,
                (cx0, cy0, cx1, cy1),
                job.crops_dir / f"{m['id']}_ctx.png",
                label=str(m["id"]),
            )

        # Guide + truth use the footprint box (not the extra-expanded isolate crop)
        L2, T2, BW2, BH2 = truth_L, truth_T, truth_W, truth_H
        gx0, gy0 = int(L2 * W), int(T2 * H)
        gx1, gy1 = int((L2 + BW2) * W), int((T2 + BH2) * H)

        pa = pixel_aspect(BW2, BH2, W, H)
        area = BW2 * BH2
        size = assert_allowed_size(m.get("size") or size_for_pixel_aspect(pa))
        quality = m.get("quality") or quality_for_area(area)

        # Do NOT overwrite plan crop with padded truth — re-setup would pad again and balloon.
        m["_truth_crop"] = [round(L2, 4), round(T2, 4), round(BW2, 4), round(BH2, 4)]
        m["_isolate_crop"] = [
            round(iso_L, 4),
            round(iso_T, 4),
            round(iso_W, 4),
            round(iso_H, 4),
        ]
        m["_pixel_aspect"] = round(pa, 3)
        m["_size"] = size
        m["_quality"] = quality
        m["_area"] = round(area, 4)
        m["_match_score"] = round(score, 4)
        m["_calibrate_fail"] = cal_fail

        color = (255, 80, 80) if cal_fail else (0, 255, 180)
        draw.rectangle([gx0, gy0, gx1 - 1, gy1 - 1], outline=color, width=max(3, W // 200))
        draw.text((gx0 + 3, gy0 + 3), f"{m['id']} {score:.2f}", fill=(255, 255, 0))

        fill = m.get("fill")
        if not fill:
            fill = "cover" if m.get("id") == "bg" or m.get("mode") == "full" else "contain"

        grounded = None
        if "grounded" in m and m["grounded"] is not None:
            grounded = _parse_grounded(m["grounded"])
        # Plan.anchor wins. Else: hang/ceiling ids → top; ungrounded wall → center; else bottom.
        if m.get("anchor"):
            anchor = str(m.get("anchor"))
        else:
            blob = f"{m.get('id','')} {m.get('name','')}".lower()
            if any(k in blob for k in ("chandelier", "吊灯", "hanging", "ceiling_lamp")):
                anchor = "top-center"
            elif grounded is False:
                anchor = "center"
            else:
                anchor = "bottom-center"

        px = [int(L2 * W), int(T2 * H), int((L2 + BW2) * W), int((T2 + BH2) * H)]
        layer_out = {
            "id": m["id"],
            "name": m.get("name", m["id"]),
            "z": m.get("z", 1),
            "file": m.get("file", f"{m['id']}.png"),
            "left": round(L2, 4),
            "top": round(T2, 4),
            "width": round(BW2, 4),
            "height": round(BH2, 4),
            "px": px,
            "anchor": anchor,
            "fill": fill,
            "note": (m.get("keep") or "")[:80],
            "size": size,
            "quality": quality,
            "keep": m.get("keep", ""),
            "remove": m.get("remove", ""),
            "match_score": round(score, 4),
            "calibrate_fail": cal_fail,
            "area": round(area, 4),
            "pixel_aspect": round(pa, 3),
            "locked": True,
        }
        if grounded is not None:
            layer_out["grounded"] = grounded
        layers.append(layer_out)
        print(
            f"{m['id']}: match={score:.3f}{' FAIL' if cal_fail else ''} "
            f"box=({L2:.3f},{T2:.3f},{BW2:.3f},{BH2:.3f}) "
            f"pa={pa:.3f} size={size} q={quality}"
        )

    truth = {
        "ref": plan.get("ref") or job.ref_path(plan).name,
        "canvas": {"w": W, "h": H, "aspect": W / H},
        "method": "pmem-layer-split-calibrate",
        "contract": "truth_boxes/_footprints are FROZEN position+size; compose only pastes into these boxes",
        "layers": layers,
    }
    job.save_truth(truth)
    job.save_plan(plan)
    fp = write_footprints(job, truth)
    guide.convert("RGB").save(job.root / "_crops_guide.png")
    fails = [L["id"] for L in layers if L.get("calibrate_fail")]
    print("wrote truth_boxes.json + _crops_guide.png +", fp.name)
    if fails:
        print("calibrate_fail:", ", ".join(fails))
    return truth
