# -*- coding: utf-8 -*-
"""Quantitative ghost QA: MAE + heatmap vs ref.

Also feeds per-layer footprint MAE back into layer_status as dirty when above
GATE.layer_ghost_mae_max — gate ok alone must not pass as restore-ready.
"""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .defaults import GATE
from .job import Job, save_json


def apply_ghost_dirty(job: Job, report: dict) -> list[str]:
    """Mark hot layers dirty when per-footprint MAE exceeds layer_ghost_mae_max.

    Returns newly dirtied ids (excluding needs_human / already dirty without change).
    """
    thr = float(GATE.get("layer_ghost_mae_max", 52.0))
    hot = report.get("hot_layers") or []
    status = job.load_status()
    layers = status.setdefault("layers", {})
    dirtied: list[str] = []
    dirty_ids = list(status.get("dirty_ids") or [])
    for lid, mae in hot:
        try:
            mae_f = float(mae)
        except (TypeError, ValueError):
            continue
        if mae_f < thr:
            continue
        prev = layers.get(lid) or {}
        if prev.get("status") == "needs_human":
            continue
        reasons = list(prev.get("reasons") or [])
        tag = f"layer_ghost_mae={mae_f:.1f}>{thr}"
        if tag not in reasons and not any(str(r).startswith("layer_ghost_mae=") for r in reasons):
            reasons.append(tag)
        # keep prior metrics; only escalate to dirty for retry
        retries = int(prev.get("retries") or 0)
        layers[lid] = {
            **prev,
            "status": "dirty",
            "reasons": reasons,
            "retries": retries,
            "metrics": {
                **(prev.get("metrics") or {}),
                "layer_ghost_mae": round(mae_f, 3),
            },
            "file": prev.get("file"),
            "source": prev.get("source", "isolate"),
        }
        if lid not in dirty_ids:
            dirty_ids.append(lid)
        dirtied.append(lid)
        print(f"GHOST→dirty {lid}: {tag}")
    # Whole-compose fail must not pull under-threshold or still-ok layers into dirty_ids.
    # pipeline retries dirty_ids; adding hot[:5] re-rolls layers that already matched.
    status["dirty_ids"] = dirty_ids
    status["ok_ids"] = [k for k, v in layers.items() if v.get("status") == "ok"]
    job.save_status(status)
    return dirtied


def ghost_qa(job: Job, *, scale: int = 2, apply_dirty: bool = True) -> dict:
    truth = job.load_truth()
    mid = job.root / "_compose_mid.png"
    if not mid.exists():
        raise FileNotFoundError("run compose first (_compose_mid.png missing)")

    cw = int(truth["canvas"]["w"])
    ch = int(truth["canvas"]["h"])
    W, H = cw * scale, ch * scale
    ref = job.open_ref({"ref": truth.get("ref")}).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)
    comp = Image.open(mid).convert("RGB").resize((W, H), Image.Resampling.LANCZOS)

    a = np.asarray(ref, dtype=np.float32)
    b = np.asarray(comp, dtype=np.float32)
    diff = np.abs(a - b)
    mae = float(diff.mean())
    mse = float(((a - b) ** 2).mean())
    psnr = 99.0 if mse < 1e-9 else float(20 * math.log10(255.0 / math.sqrt(mse)))

    heat = diff.mean(axis=2)
    heat_u8 = (heat / max(heat.max(), 1e-6) * 255).astype(np.uint8)
    heat_rgb = np.stack([heat_u8, (255 - heat_u8) // 2, np.zeros_like(heat_u8)], axis=2)
    Image.fromarray(heat_rgb).save(job.root / "_ghost_heatmap.png")

    # per-layer MAE inside footprint (rough attribution)
    per = {}
    for L in truth["layers"]:
        if L["id"] == "bg":
            continue
        x0 = int(L["left"] * W)
        y0 = int(L["top"] * H)
        x1 = int((L["left"] + L["width"]) * W)
        y1 = int((L["top"] + L["height"]) * H)
        patch = diff[y0:y1, x0:x1]
        if patch.size:
            per[L["id"]] = round(float(patch.mean()), 3)

    ranked = sorted(per.items(), key=lambda kv: -kv[1])[:8]
    level = "ok"
    if mae >= GATE["ghost_mae_fail"]:
        level = "fail"
    elif mae >= GATE["ghost_mae_warn"]:
        level = "warn"

    report = {
        "mae": round(mae, 3),
        "psnr": round(psnr, 3),
        "level": level,
        "thresholds": {
            "warn": GATE["ghost_mae_warn"],
            "fail": GATE["ghost_mae_fail"],
        },
        "hot_layers": ranked,
        "heatmap": "_ghost_heatmap.png",
        "preview": "_compose_preview.png",
    }
    save_json(job.root / "_ghost_qa.json", report)
    print(
        f"ghost QA: mae={report['mae']} psnr={report['psnr']} level={level} "
        f"hot={ranked[:3]}"
    )
    if apply_dirty:
        dirtied = apply_ghost_dirty(job, report)
        if dirtied:
            print(f"ghost dirty feedback: {dirtied} (thr={GATE.get('layer_ghost_mae_max')})")
        elif level == "fail":
            print(
                "ghost level=fail — do NOT treat as shippable; "
                "retry hot layers or tighten footprints"
            )
    return report
