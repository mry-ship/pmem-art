#!/usr/bin/env python3
"""Blind Absolute-5D VLM scoring for pmem_art_images_v7_32bots_showcase.html images.

Uses .memory-art/vlm_judge.local.yaml (gitignored). Does NOT call GenerateImage.

Usage:
  cd /Users/yanghu/Desktop/pmem-art
  export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
  python3 scripts/score_v7_showcase_vlm.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS))

IMAGES_ROOT = Path(__import__("os").environ.get("PMEM_ART_IMAGES_ROOT", "/Users/yanghu/Desktop/pmem-art-images"))
HTML_PATH = IMAGES_ROOT / "pmem_art_images_v7_32bots_showcase.html"
OUT_JSON = IMAGES_ROOT / "v7_showcase_vlm_scores.json"
OUT_MD = IMAGES_ROOT / "v7_showcase_vlm_scores.md"

from vlm_judge import (  # noqa: E402
    call_vision_judge,
    load_vlm_judge_config,
    observations_from_vlm_payload,
    vlm_judge_status,
)
from skills_kit.scoring import parse_5d_dims  # noqa: E402
from absolute_5d_scorer import HEURISTIC_STOP_THRESHOLD, absolute_5d  # noqa: E402

# Absolute quality — same medium weights for every plate (fair cross-scale compare).
ABS_WEIGHTS = {
    "composition": 0.20,
    "lighting_color": 0.25,
    "perspective_anatomy": 0.20,
    "texture_detail": 0.20,
    "spec_style": 0.15,
}


def _list_html_images() -> list[str]:
    html = HTML_PATH.read_text(encoding="utf-8", errors="ignore")
    srcs = sorted(set(re.findall(r'src="(generated_v7/[^"]+\.(?:jpg|jpeg|png|webp))"', html)))
    return srcs


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
    for slug in ("night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon", "concept_ishtar"):
        if slug in name:
            return slug.replace("concept_ishtar", "ishtar_canyon")
    if "style_ref_01" in name:
        return "night_city"
    if "style_ref_02" in name:
        return "pastel_sketch"
    if "style_ref_03" in name:
        return "sunlit_portrait"
    if "web_ref_01" in name:
        return "ishtar_canyon"
    return "?"


def main() -> int:
    cfg = load_vlm_judge_config(REPO_ROOT)
    status = vlm_judge_status(REPO_ROOT)
    print("VLM status:", {k: status[k] for k in ("active", "provider", "model", "base_url", "api_key_present")})
    if not status.get("active"):
        print("FAIL: VLM not configured (.memory-art/vlm_judge.local.yaml)")
        return 1

    rels = _list_html_images()
    print(f"Scoring {len(rels)} showcase images with model={cfg.get('model')}")
    scale_prof = {"scale": "medium", "dim_weights": ABS_WEIGHTS, "target_score_threshold": HEURISTIC_STOP_THRESHOLD}

    results = []
    failed = []
    for i, rel in enumerate(rels, 1):
        path = IMAGES_ROOT / rel
        name = Path(rel).name
        role = _role_of(name)
        case = _case_of(name)
        print(f"[{i}/{len(rels)}] {name} …", flush=True)
        row: dict = {
            "file": rel,
            "name": name,
            "case": case,
            "role": role,
            "ok": False,
        }
        # Also record heuristic Absolute-5D for side-by-side
        try:
            heur = absolute_5d(str(path), api_scale="medium")
            row["heuristic_a5d"] = heur["score"]
            row["heuristic_dims"] = heur["dims"]
        except Exception as e:
            row["heuristic_error"] = str(e)

        try:
            obs = call_vision_judge(
                path,
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
                weighted = sum(float(p.get(k, 0)) * ABS_WEIGHTS[k] for k in ABS_WEIGHTS)
                weighted = round(weighted, 2)
            row.update(
                {
                    "ok": True,
                    "vlm_score": weighted,
                    "vlm_dims_str": dims_str,
                    "vlm_dims": parsed.get("parsed") or {},
                    "defects": obs.get("defects") or "",
                    "strengths": obs.get("strengths") or "",
                    "next_fix": obs.get("next_fix") or "",
                    "model": obs.get("model") or cfg.get("model"),
                }
            )
            print(f"      VLM={weighted}  heur={row.get('heuristic_a5d')}  {dims_str}")
        except Exception as e:
            row["error"] = f"{type(e).__name__}: {e}"
            failed.append(row)
            print(f"      FAIL {row['error'][:160]}")
            time.sleep(1.5)
        results.append(row)
        # gentle pacing
        time.sleep(0.4)

    # Baselines per case for Δ
    base_by_case = {
        r["case"]: r["vlm_score"]
        for r in results
        if r.get("ok") and r.get("role") == "baseline_ref" and r.get("vlm_score") is not None
    }
    for r in results:
        if r.get("ok") and r.get("vlm_score") is not None and r["case"] in base_by_case:
            r["vlm_delta_vs_ref"] = round(float(r["vlm_score"]) - float(base_by_case[r["case"]]), 2)

    report = {
        "version": "v7_showcase_vlm",
        "model": cfg.get("model"),
        "provider": cfg.get("provider"),
        "base_url": cfg.get("base_url"),
        "weights": ABS_WEIGHTS,
        "note": "Absolute blind VLM 5D; same medium weights for all plates. Not V8 generation proof.",
        "n": len(results),
        "n_ok": sum(1 for r in results if r.get("ok")),
        "n_fail": len(failed),
        "baselines": base_by_case,
        "results": results,
    }
    OUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown table
    lines = [
        f"# V7 Showcase VLM 盲评（{cfg.get('model')}）",
        "",
        f"- 权重（绝对品质）: {ABS_WEIGHTS}",
        f"- 成功 {report['n_ok']}/{report['n']} · 失败 {report['n_fail']}",
        "- 旧 V2 剧本分不可横比；本表为独立视觉模型绝对分",
        "",
        "| case | role | file | VLM | Δvs原图 | heur A5D | defects |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for r in results:
        defects = (r.get("defects") or r.get("error") or "").replace("|", "/").replace("\n", " ")[:80]
        lines.append(
            f"| {r.get('case')} | {r.get('role')} | `{r.get('name')}` | "
            f"{r.get('vlm_score') if r.get('vlm_score') is not None else '—'} | "
            f"{r.get('vlm_delta_vs_ref') if r.get('vlm_delta_vs_ref') is not None else '—'} | "
            f"{r.get('heuristic_a5d') if r.get('heuristic_a5d') is not None else '—'} | {defects} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nJSON → {OUT_JSON}")
    print(f"MD   → {OUT_MD}")
    print(f"Summary ok={report['n_ok']}/{report['n']} baselines={base_by_case}")
    return 0 if report["n_fail"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
