#!/usr/bin/env python3
"""Dual Absolute-5D scoring for v3 + v6 showcase HTML images (offline + VLM).

Extracts unique <img alt=… src=data:…> plates from the showcase HTML, scores each
with offline checklist Absolute-5D and independent VLM, then writes JSON/MD.

Usage:
  cd /Users/yanghu/Desktop/pmem-art
  export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
  # offline only (fast):
  python3 scripts/score_v3_v6_showcase_dual.py --offline-only
  # full dual track (override model if desired):
  PMEM_VLM_MODEL=gpt-6-sol python3 scripts/score_v3_v6_showcase_dual.py
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS))

IMAGES_ROOT = Path(os.environ.get("PMEM_ART_IMAGES_ROOT", "/Users/yanghu/Desktop/pmem-art-images"))
V3_HTML = Path("/Users/yanghu/Desktop/pmem_art_images_v3_16bots_showcase.html")
V6_HTML = IMAGES_ROOT / "pmem_art_images_v6_32bots_showcase.html"

from absolute_5d_scorer import HEURISTIC_STOP_THRESHOLD, absolute_5d  # noqa: E402
from skills_kit.scoring import parse_5d_dims  # noqa: E402
from vlm_judge import call_vision_judge, load_vlm_judge_config, vlm_judge_status  # noqa: E402

ABS_WEIGHTS = {
    "composition": 0.20,
    "lighting_color": 0.25,
    "perspective_anatomy": 0.20,
    "texture_detail": 0.20,
    "spec_style": 0.15,
}


def _role_of(name: str) -> str:
    if name.startswith("style_ref_") or name.startswith("web_ref_"):
        return "baseline_ref"
    if "_low_best" in name:
        return "low_best"
    if "_medium_best" in name:
        return "medium_best"
    if "_high_best" in name:
        return "high_best"
    if "recompose_bold" in name:
        return "recompose_bold"
    if "_recompose" in name:
        return "recompose"
    if "_low" in name:
        return "low"
    if "_medium" in name:
        return "medium"
    if "_high" in name:
        return "high"
    return "other"


def _case_of(name: str) -> str:
    for slug in ("night_city", "pastel_sketch", "sunlit_portrait", "ishtar", "concept_ishtar"):
        if slug in name:
            if "ishtar" in slug:
                return "ishtar_canyon"
            return slug
    if "style_ref_01" in name:
        return "night_city"
    if "style_ref_02" in name:
        return "pastel_sketch"
    if "style_ref_03" in name:
        return "sunlit_portrait"
    if "web_ref_01" in name:
        return "ishtar_canyon"
    return "?"


def extract_unique(html_path: Path, out_dir: Path) -> list[dict]:
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    seen: set[str] = set()
    for m in re.finditer(r"<img\b[^>]*>", html, re.I):
        tag = m.group(0)
        alt_m = re.search(r'\balt="([^"]+)"', tag)
        src_m = re.search(r'\bsrc="(data:image/([^;]+);base64,([^"]+))"', tag)
        if not src_m:
            continue
        name = Path((alt_m.group(1) if alt_m else "").strip()).name
        if not name:
            continue
        if name in seen:
            continue
        seen.add(name)
        raw = base64.b64decode(src_m.group(3))
        path = out_dir / name
        path.write_bytes(raw)
        try:
            from PIL import Image

            with Image.open(path) as im:
                w, h = im.size
        except Exception:
            w = h = 0
        rows.append(
            {
                "name": name,
                "path": str(path),
                "bytes": len(raw),
                "width": w,
                "height": h,
                "case": _case_of(name),
                "role": _role_of(name),
            }
        )
    rows.sort(key=lambda r: (r["case"], r["role"], r["name"]))
    return rows


def score_offline(rows: list[dict]) -> None:
    for i, r in enumerate(rows, 1):
        print(f"[offline {i}/{len(rows)}] {r['name']} …", flush=True)
        try:
            heur = absolute_5d(r["path"], api_scale="medium")
            r["offline_score"] = heur["score"]
            r["offline_dims"] = heur["dims"]
            r["offline_ok"] = True
            print(f"      offline={heur['score']}  dims={heur['dims']}", flush=True)
        except Exception as e:
            r["offline_ok"] = False
            r["offline_error"] = f"{type(e).__name__}: {e}"
            print(f"      FAIL {r['offline_error'][:160]}", flush=True)


def score_vlm(rows: list[dict], model_override: str | None) -> dict:
    cfg = load_vlm_judge_config(REPO_ROOT)
    if model_override:
        cfg = dict(cfg)
        cfg["model"] = model_override
    status = vlm_judge_status(REPO_ROOT)
    print(
        "VLM status:",
        {k: status[k] for k in ("active", "provider", "model", "base_url", "api_key_present")},
        "override=",
        cfg.get("model"),
        flush=True,
    )
    if not status.get("active"):
        raise SystemExit("FAIL: VLM not configured")

    scale_prof = {
        "scale": "medium",
        "dim_weights": ABS_WEIGHTS,
        "target_score_threshold": HEURISTIC_STOP_THRESHOLD,
    }
    n_ok = 0
    for i, r in enumerate(rows, 1):
        print(f"[vlm {i}/{len(rows)}] {r['name']} …", flush=True)
        try:
            obs = call_vision_judge(
                Path(r["path"]),
                cfg=cfg,
                scale_prof=scale_prof,
                goal="绝对品质盲评（忽略档位任务，只看画面本身好坏）",
                module="",
                round_num=1,
            )
            dims_str = obs.get("dims") or ""
            parsed = parse_5d_dims(dims_str, ABS_WEIGHTS) or {}
            weighted = parsed.get("weighted_score")
            if weighted is None and parsed.get("parsed"):
                p = parsed["parsed"]
                weighted = round(sum(float(p.get(k, 0)) * ABS_WEIGHTS[k] for k in ABS_WEIGHTS), 2)
            r.update(
                {
                    "vlm_ok": True,
                    "vlm_score": weighted,
                    "vlm_dims_str": dims_str,
                    "vlm_dims": parsed.get("parsed") or {},
                    "defects": obs.get("defects") or "",
                    "strengths": obs.get("strengths") or "",
                    "next_fix": obs.get("next_fix") or "",
                    "vlm_model": obs.get("model") or cfg.get("model"),
                }
            )
            n_ok += 1
            off = r.get("offline_score")
            delta = None if off is None or weighted is None else round(float(off) - float(weighted), 2)
            r["delta_off_minus_vlm"] = delta
            print(f"      VLM={weighted}  off={off}  Δ={delta}  {dims_str}", flush=True)
        except Exception as e:
            r["vlm_ok"] = False
            r["vlm_error"] = f"{type(e).__name__}: {e}"
            print(f"      FAIL {r['vlm_error'][:200]}", flush=True)
            time.sleep(1.5)
        time.sleep(0.35)
    return {"model": cfg.get("model"), "n_ok": n_ok}


def summarize(set_id: str, rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("offline_ok") and r.get("vlm_ok") and r.get("vlm_score") is not None]
    deltas = [float(r["delta_off_minus_vlm"]) for r in ok if r.get("delta_off_minus_vlm") is not None]
    mae = round(sum(abs(d) for d in deltas) / len(deltas), 3) if deltas else None
    mean_off = round(sum(float(r["offline_score"]) for r in ok) / len(ok), 3) if ok else None
    mean_vlm = round(sum(float(r["vlm_score"]) for r in ok) / len(ok), 3) if ok else None
    within1 = sum(1 for d in deltas if abs(d) <= 1.0)
    return {
        "set": set_id,
        "n": len(rows),
        "n_paired": len(ok),
        "mean_offline": mean_off,
        "mean_vlm": mean_vlm,
        "mae_off_vs_vlm": mae,
        "within_1pt": f"{within1}/{len(deltas)}" if deltas else None,
        "mean_bias_off_minus_vlm": round(sum(deltas) / len(deltas), 3) if deltas else None,
        "min_w": min((r["width"] for r in rows), default=0),
        "max_w": max((r["width"] for r in rows), default=0),
    }


def write_outputs(set_id: str, rows: list[dict], meta: dict, out_stem: Path) -> None:
    report = {
        "version": f"{set_id}_showcase_dual_a5d",
        "weights": ABS_WEIGHTS,
        "meta": meta,
        "summary": summarize(set_id, rows),
        "results": rows,
    }
    out_json = Path(str(out_stem) + ".json")
    out_md = Path(str(out_stem) + ".md")
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# {set_id.upper()} Showcase · Offline Absolute-5D vs VLM",
        "",
        f"- model: `{meta.get('vlm_model')}`",
        f"- paired: {report['summary']}",
        f"- note: {meta.get('note', '')}",
        "",
        "| case | role | file | W×H | offline | VLM | Δ(off−vlm) | defects |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for r in rows:
        defects = (r.get("defects") or r.get("vlm_error") or r.get("offline_error") or "").replace("|", "/")
        defects = defects.replace("\n", " ")[:90]
        lines.append(
            f"| {r.get('case')} | {r.get('role')} | `{r.get('name')}` | "
            f"{r.get('width')}×{r.get('height')} | "
            f"{r.get('offline_score') if r.get('offline_score') is not None else '—'} | "
            f"{r.get('vlm_score') if r.get('vlm_score') is not None else '—'} | "
            f"{r.get('delta_off_minus_vlm') if r.get('delta_off_minus_vlm') is not None else '—'} | "
            f"{defects} |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_json}", flush=True)
    print(f"Wrote {out_md}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline-only", action="store_true")
    ap.add_argument("--set", choices=("v3", "v6", "both"), default="both")
    ap.add_argument("--model", default=os.environ.get("PMEM_VLM_MODEL", "gpt-6-sol"))
    args = ap.parse_args()

    jobs = []
    if args.set in ("v3", "both"):
        jobs.append(("v3", V3_HTML, IMAGES_ROOT / "extracted_v3_showcase", IMAGES_ROOT / "v3_showcase_dual_a5d"))
    if args.set in ("v6", "both"):
        jobs.append(("v6", V6_HTML, IMAGES_ROOT / "extracted_v6_showcase", IMAGES_ROOT / "v6_showcase_dual_a5d"))

    all_summaries = []
    for set_id, html, out_dir, stem in jobs:
        if not html.exists():
            print(f"MISSING HTML: {html}", flush=True)
            continue
        print(f"\n=== {set_id} extract from {html} ===", flush=True)
        rows = extract_unique(html, out_dir)
        print(f"unique images: {len(rows)}", flush=True)
        score_offline(rows)
        meta = {
            "html": str(html),
            "extract_dir": str(out_dir),
            "offline_only": args.offline_only,
            "note": (
                "v6 HTML embeds half-res JPEG thumbs (~200–360px); v3 embeds near-full plates. "
                "Offline/VLM both score the embedded bytes as shown in the showcase."
            ),
        }
        if not args.offline_only:
            vmeta = score_vlm(rows, args.model)
            meta["vlm_model"] = vmeta["model"]
            meta["vlm_n_ok"] = vmeta["n_ok"]
        else:
            meta["vlm_model"] = None
        write_outputs(set_id, rows, meta, stem)
        all_summaries.append(summarize(set_id, rows))

    print("\n=== SUMMARIES ===", flush=True)
    print(json.dumps(all_summaries, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
