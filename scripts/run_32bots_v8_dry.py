#!/usr/bin/env python3
"""
V8 32-bot dry-run (NO image generation).

- Absolute-5D v9 checklist (gpt-6-sol 0/1/2) is the offline score track
- STOP = HEURISTIC_STOP_THRESHOLD (8.50), not legacy showcase 9.60
- Intent / Δ are diagnostic (not semantic VLM)
- high / recompose / bold enforce min_rounds ≥ 2
- R2+ prompt rewrite path exercised via rewrite_prompt_from_defects
- Lock-phrase preflight on bot_tasks_v8 + best overlays

Usage:
  cd /Users/yanghu/Desktop/pmem-art
  export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
  python3 scripts/run_32bots_v8_dry.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS))

from skills_kit import (  # noqa: E402
    check_scale_task_text,
    compose_style_first_prompt,
    find_affirmative_lock_hits,
    get_converge_scale_profile,
    strip_affirmative_locks_from_prompt,
)
from absolute_5d_scorer import (  # noqa: E402
    HEURISTIC_STOP_THRESHOLD,
    NEUTRAL_PRIOR,
    intent_check,
    rewrite_prompt_from_defects,
    score_checklist,
)


def _load_json(name: str) -> dict:
    p = REPO_ROOT / name
    if not p.is_file():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def _best_overlay(best_doc: dict, bot: dict) -> str:
    mode = bot.get("prompt_mode") or "none"
    if mode == "style_jump":
        by = (best_doc.get("by_scale") or {}).get("recompose_bold") or {}
        case = bot.get("case_id") or ""
        return str(by.get(case) or by.get("_default") or "")
    if mode != "best":
        return ""
    api = bot.get("api_scale") or "medium"
    case = bot.get("case_id") or ""
    by = (best_doc.get("by_scale") or {}).get(api) or {}
    return str(by.get(case) or by.get("_default") or "")


def _sim_metrics(api: str, round_num: int) -> dict[str, float]:
    """Synthetic plates for dry-run — checklist-friendly fields (R1 soft, R2 near STOP)."""
    if api == "low":
        return {
            "contrast": 0.28, "edge_energy": 0.32, "cold_warm_separation": 0.22,
            "texture_hf": 0.30, "color_richness": 0.28, "midtone_mass": 0.55,
            "sharpness": 0.40, "resolution_score": 0.55, "mushiness": 0.38,
            "edge_coherence": 0.40, "clarity": 0.38, "clip_extreme": 0.03,
            "short_side": 720, "salience_gap": 0.20, "read_256": 0.35,
            "melt_ratio": 0.10, "grid_imbalance": 2.2, "edge_density_ratio": 1.2,
            "material_spread": 0.28, "wb_dev": 9.0, "crop_pressure": 0.40,
            "depth_cue": 0.25, "subj_bg_contrast_gap": 0.15, "noise_as_structure": 0.25,
        }
    if api == "medium":
        return {
            "contrast": 0.40, "edge_energy": 0.42, "cold_warm_separation": 0.42,
            "texture_hf": 0.38, "color_richness": 0.40, "midtone_mass": 0.55,
            "sharpness": 0.50, "resolution_score": 0.65, "mushiness": 0.30,
            "edge_coherence": 0.50, "clarity": 0.48, "clip_extreme": 0.02,
            "short_side": 1024, "salience_gap": 0.26, "read_256": 0.48,
            "melt_ratio": 0.06, "grid_imbalance": 1.9, "edge_density_ratio": 1.4,
            "material_spread": 0.38, "wb_dev": 7.0, "crop_pressure": 0.34,
            "depth_cue": 0.38, "subj_bg_contrast_gap": 0.20, "noise_as_structure": 0.18,
        }
    if round_num < 2:
        return {
            "contrast": 0.22, "edge_energy": 0.24, "cold_warm_separation": 0.18,
            "texture_hf": 0.18, "color_richness": 0.25, "midtone_mass": 0.50,
            "sharpness": 0.22, "resolution_score": 0.25, "mushiness": 0.70,
            "edge_coherence": 0.22, "clarity": 0.20, "clip_extreme": 0.06,
            "short_side": 512, "salience_gap": 0.12, "read_256": 0.20,
            "melt_ratio": 0.22, "grid_imbalance": 3.5, "edge_density_ratio": 0.95,
            "material_spread": 0.15, "wb_dev": 14.0, "crop_pressure": 0.55,
            "depth_cue": 0.12, "subj_bg_contrast_gap": 0.08, "noise_as_structure": 0.50,
        }
    return {
        "contrast": 0.92, "edge_energy": 0.90, "cold_warm_separation": 0.88,
        "texture_hf": 0.88, "color_richness": 0.88, "midtone_mass": 0.62,
        "sharpness": 0.92, "resolution_score": 0.95, "mushiness": 0.08,
        "edge_coherence": 0.88, "clarity": 0.88, "clip_extreme": 0.005,
        "short_side": 1536, "salience_gap": 0.42, "read_256": 0.85,
        "melt_ratio": 0.02, "grid_imbalance": 1.3, "edge_density_ratio": 2.0,
        "material_spread": 0.70, "wb_dev": 4.0, "crop_pressure": 0.18,
        "depth_cue": 0.65, "subj_bg_contrast_gap": 0.40, "noise_as_structure": 0.05,
    }


def run_bot(bot: dict, best_doc: dict) -> dict:
    api = str(bot.get("api_scale") or "medium")
    mode = str(bot.get("prompt_mode") or "none")
    recompose_dir = str(bot.get("recompose_dir") or "")
    min_r = int(bot.get("min_rounds_before_stop") or (2 if api in ("high", "recompose") else 1))
    if mode == "style_jump":
        min_r = max(min_r, 2)

    pre = check_scale_task_text(
        scale=api,
        goal=str(bot.get("goal") or ""),
        prompt=str(bot.get("gen_description") or ""),
        best_direction=_best_overlay(best_doc, bot),
        recompose_dir=recompose_dir,
        recompose_bold=(mode == "style_jump"),
    )
    if not pre["ok"]:
        return {"bot_id": bot["bot_id"], "ok": False, "phase": "preflight", "issues": pre["issues"]}

    # Forbidden V8 lock / empty-prop phrases in task text
    blob = " ".join(
        str(bot.get(k) or "") for k in ("goal", "gen_description", "recompose_dir")
    )
    for bad in ("严格保留DNA", "参考垫图一致性高", "构图：锁死", "叙事道具只保留原图已有"):
        if bad in blob:
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": "lock_scan",
                "issues": [f"forbidden phrase: {bad}"],
            }

    if api == "high" and "50" not in str(bot.get("goal") or "") and "80" not in str(bot.get("goal") or ""):
        return {
            "bot_id": bot["bot_id"],
            "ok": False,
            "phase": "high_budget",
            "issues": ["high goal missing 50–80% band"],
        }

    if bot["slug"] == "night_city" and api == "recompose" and mode != "style_jump":
        g = str(bot.get("goal") or "") + str(bot.get("recompose_dir") or "")
        if "乌篷" not in g and "仰" not in g:
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": "recompose_shot",
                "issues": ["night recompose missing 乌篷/仰桥-class camera"],
            }
        if "高空俯瞰" in g and "左下飞檐" in g:
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": "recompose_shot",
                "issues": ["night recompose still has old overhead DNA"],
            }

    if mode == "style_jump" and recompose_dir.strip():
        # bold must not reuse recompose camera dir
        return {
            "bot_id": bot["bot_id"],
            "ok": False,
            "phase": "bold_split",
            "issues": ["recompose_bold must not carry recompose_dir camera mix"],
        }

    prof = get_converge_scale_profile(
        api,
        recompose_dir=recompose_dir,
        goal=str(bot.get("goal") or ""),
        ref_image=str(bot.get("ref_image") or ""),
        module=str(bot.get("module") or ""),
    )
    min_r = max(min_r, int(prof.get("min_rounds_before_stop") or 1))

    base = " | ".join(
        x for x in (bot.get("gen_description"), bot.get("goal"), _best_overlay(best_doc, bot)) if x
    )
    base = strip_affirmative_locks_from_prompt(base, scale=api)
    composed = compose_style_first_prompt(base, prof)
    lock_hits = find_affirmative_lock_hits(composed)
    if lock_hits and api in ("high", "recompose"):
        return {
            "bot_id": bot["bot_id"],
            "ok": False,
            "phase": "compose",
            "issues": [f"composed prompt still has locks: {lock_hits}"],
            "prompt": composed,
        }

    # Synthetic baseline (same checklist Absolute-5D ruler)
    base_m = _sim_metrics("medium", 2)
    base_pack = score_checklist(base_m, api_scale=api, prompt_mode=mode)
    base_score = {
        "score": base_pack["score"],
        "dims": {
            k: (base_pack["dims"][k] if base_pack["dims"][k] is not None else NEUTRAL_PRIOR)
            for k in base_pack["dims"]
        },
        "metrics": base_m,
    }

    history = []
    prompt_r = composed
    for r in range(1, min_r + 1):
        m = _sim_metrics(api, r)
        pack = score_checklist(m, api_scale=api, prompt_mode=mode)
        dims = {
            k: (pack["dims"][k] if pack["dims"][k] is not None else NEUTRAL_PRIOR)
            for k in pack["dims"]
        }
        score = pack["score"]
        bot_pack = {
            "score": score,
            "dims": dims,
            "metrics": m,
            "vs_ref": {"struct": 0.85 if r == 1 else 0.35, "mse": 200.0 if r == 1 else 900.0},
            "struct": 0.85 if r == 1 else 0.35,
        }
        intent = intent_check(
            api_scale=api,
            prompt_mode=mode,
            bot_score=bot_pack,
            baseline_score=base_score,
            recompose_dir=recompose_dir,
        )
        defects = []
        if not intent.get("pass"):
            defects.append(str(intent.get("reason") or "intent fail"))
        if r == 1 and score < HEURISTIC_STOP_THRESHOLD:
            defects.append(f"Absolute-5D 未达 {HEURISTIC_STOP_THRESHOLD}")
        if r >= 2 or defects:
            prompt_r = rewrite_prompt_from_defects(
                composed,
                defects=defects or ["细节可再锐"],
                intent=intent,
                api_scale=api,
                recompose_dir=recompose_dir,
            )
        decision = (
            "STOP_TARGET_REACHED"
            if (score >= HEURISTIC_STOP_THRESHOLD and r >= min_r and intent.get("pass"))
            else "CONTINUE_NEXT_ROUND"
        )
        if r < min_r and decision == "STOP_TARGET_REACHED":
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": "min_rounds",
                "issues": [f"tried STOP at R{r} but min_rounds={min_r}"],
                "history": history,
            }
        history.append(
            {
                "round": r,
                "score": score,
                "baseline": base_score["score"],
                "delta": round(score - base_score["score"], 2),
                "intent": intent,
                "prompt_rewritten": "【回流修正】" in prompt_r,
                "decision": decision,
            }
        )
        if decision == "STOP_TARGET_REACHED":
            break

    if api in ("high", "recompose") and len(history) < 2:
        return {
            "bot_id": bot["bot_id"],
            "ok": False,
            "phase": "min_rounds",
            "issues": [f"only {len(history)} rounds; need ≥2"],
            "history": history,
        }

    # high/recompose must have rewritten after R1 when continuing
    if api in ("high", "recompose") and len(history) >= 2:
        if not any(h.get("prompt_rewritten") for h in history[1:]):
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": "reflow",
                "issues": ["R2+ missing defect→prompt rewrite"],
                "history": history,
            }

    return {
        "bot_id": bot["bot_id"],
        "ok": True,
        "display_scale": bot.get("display_scale"),
        "api_scale": api,
        "min_rounds": min_r,
        "rounds_run": len(history),
        "prompt": composed,
        "prompt_r_last": prompt_r,
        "history": history,
        "final_decision": history[-1]["decision"] if history else "",
    }


def main() -> int:
    tasks = _load_json("bot_tasks_v8.json")
    best = _load_json("best_prompts_by_scale.json")
    bots = tasks.get("bots") or []
    failed = []
    print(f"V8 dry-run · {len(bots)} bots · Absolute-5D · skills_kit={REPO_ROOT / 'skills_kit'}")
    for bot in bots:
        res = run_bot(bot, best)
        mark = "OK" if res.get("ok") else "FAIL"
        print(
            f"[{mark}] {res.get('bot_id')} {bot.get('display_scale')} "
            f"api={bot.get('api_scale')} rounds={res.get('rounds_run', 0)}"
        )
        if not res.get("ok"):
            failed.append(res)
            for iss in res.get("issues") or []:
                print(f"       · {iss}")
    print(f"\nSummary: {len(bots) - len(failed)}/{len(bots)} OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
