# -*- coding: utf-8 -*-
"""Auto gate: mark ok / dirty from compose metrics + sprite alpha stats."""
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
            if lid != "bg":
                if asp > GATE["asp_err_max"]:
                    reasons.append(f"asp_err={asp:.3f}>{GATE['asp_err_max']}")
                if fill < GATE["fill_min"]:
                    reasons.append(f"fill={fill:.3f}<{GATE['fill_min']}")
                if fill > GATE["fill_max"]:
                    reasons.append(f"fill={fill:.3f}>{GATE['fill_max']}")
                src = resolve_sprite(job, layer)
                if src:
                    am = _alpha_mean(src)
                    if am < GATE["alpha_mean_min"]:
                        reasons.append(f"alpha_mean={am:.3f}<{GATE['alpha_mean_min']}")
                    if am > GATE["alpha_mean_max"]:
                        reasons.append(f"alpha_mean={am:.3f}>{GATE['alpha_mean_max']} (possible tile bleed)")
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
