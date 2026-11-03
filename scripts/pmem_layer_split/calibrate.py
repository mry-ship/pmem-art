# -*- coding: utf-8 -*-
"""Export crops + template-match footprints back onto the ref."""
from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from .defaults import GATE
from .job import (
    Job,
    modules_of,
    pixel_aspect,
    quality_for_area,
    size_for_pixel_aspect,
    assert_allowed_size,
)


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


def setup_and_calibrate(job: Job, *, skip_match: bool = False) -> dict:
    plan = job.load_plan()
    ref = job.open_ref(plan)
    W, H = ref.size
    ref_rgb = np.array(ref.convert("RGB"))
    job.crops_dir.mkdir(exist_ok=True)

    guide = ref.copy()
    draw = ImageDraw.Draw(guide)
    layers = []
    min_score = GATE["match_score_min"]

    for m in modules_of(plan):
        L, T, BW, BH = _clamp_box(*_norm_box_from_plan(m))
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

        # refresh crop from matched box
        cx0, cy0 = int(L2 * W), int(T2 * H)
        cx1, cy1 = int((L2 + BW2) * W), int((T2 + BH2) * H)
        crop2 = ref.crop((cx0, cy0, max(cx0 + 1, cx1), max(cy0 + 1, cy1)))
        crop2.save(crop_path)

        pa = pixel_aspect(BW2, BH2, W, H)
        area = BW2 * BH2
        size = assert_allowed_size(m.get("size") or size_for_pixel_aspect(pa))
        quality = m.get("quality") or quality_for_area(area)

        m["crop"] = [round(L2, 4), round(T2, 4), round(BW2, 4), round(BH2, 4)]
        m["_pixel_aspect"] = round(pa, 3)
        m["_size"] = size
        m["_quality"] = quality
        m["_area"] = round(area, 4)
        m["_match_score"] = round(score, 4)
        m["_calibrate_fail"] = cal_fail

        color = (255, 80, 80) if cal_fail else (0, 255, 180)
        draw.rectangle([cx0, cy0, cx1 - 1, cy1 - 1], outline=color, width=2)
        draw.text((cx0 + 3, cy0 + 3), f"{m['id']} {score:.2f}", fill=(255, 255, 0))

        fill = m.get("fill")
        if not fill:
            fill = "cover" if m.get("id") == "bg" or m.get("mode") == "full" else "contain"

        layers.append(
            {
                "id": m["id"],
                "name": m.get("name", m["id"]),
                "z": m.get("z", 1),
                "file": m.get("file", f"{m['id']}.png"),
                "left": round(L2, 4),
                "top": round(T2, 4),
                "width": round(BW2, 4),
                "height": round(BH2, 4),
                "anchor": "bottom-center",
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
                **(
                    {"grounded": _parse_grounded(m["grounded"])}
                    if "grounded" in m and m["grounded"] is not None
                    else {}
                ),
            }
        )
        print(
            f"{m['id']}: match={score:.3f}{' FAIL' if cal_fail else ''} "
            f"box=({L2:.3f},{T2:.3f},{BW2:.3f},{BH2:.3f}) "
            f"pa={pa:.3f} size={size} q={quality}"
        )

    truth = {
        "ref": plan.get("ref") or job.ref_path(plan).name,
        "canvas": {"w": W, "h": H, "aspect": W / H},
        "method": "pmem-layer-split-calibrate",
        "layers": layers,
    }
    job.save_truth(truth)
    job.save_plan(plan)
    guide.convert("RGB").save(job.root / "_crops_guide.png")
    fails = [L["id"] for L in layers if L.get("calibrate_fail")]
    print("wrote truth_boxes.json + _crops_guide.png")
    if fails:
        print("calibrate_fail:", ", ".join(fails))
    return truth
