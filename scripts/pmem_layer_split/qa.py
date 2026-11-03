# -*- coding: utf-8 -*-
"""Quantitative ghost QA: MAE + heatmap vs ref."""
from __future__ import annotations

import math

import numpy as np
from PIL import Image

from .defaults import GATE
from .job import Job, save_json


def ghost_qa(job: Job, *, scale: int = 2) -> dict:
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
    return report
