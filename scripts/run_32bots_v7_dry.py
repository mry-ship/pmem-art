#!/usr/bin/env python3
"""
V7 32-bot dry-run runner (NO image generation).

- Loads Desktop skills_kit via PYTHONPATH = repo root
- Respects min_rounds_before_stop (high / recompose / bold ≥ 2)
- Strips affirmative DNA locks when composing prompts
- Applies best overlays from best_prompts_by_scale.json (additive only)
- Uses v7_image_scorer (no struct→9.60 floor)

Usage:
  cd /Users/yanghu/Desktop/pmem-art
  PYTHONPATH=. python3 scripts/run_32bots_v7_dry.py
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
    parse_5d_dims,
    strip_affirmative_locks_from_prompt,
)
from skills_kit.judge_auto import auto_vlm_judge_image  # noqa: E402
from v7_image_scorer import score_v7  # noqa: E402


def _load_json(name: str) -> dict:
    p = REPO_ROOT / name
    if not p.is_file():
        raise FileNotFoundError(p)
    return json.loads(p.read_text(encoding="utf-8"))


def _best_overlay(best_doc: dict, bot: dict) -> str:
    mode = bot.get("prompt_mode") or "none"
    if mode not in ("best",):
        return ""
    api = bot.get("api_scale") or "medium"
    case = bot.get("case_id") or ""
    by = (best_doc.get("by_scale") or {}).get(api) or {}
    return str(by.get(case) or by.get("_default") or "")


def _simulate_dims(api: str, round_num: int) -> str:
    # Dry-run synthetic dims: R1 under drama, R2 stronger lighting for high-tier.
    if api == "low":
        return "构图9.2/光影8.8/透视9.0/质感9.1/风格9.0"
    if api == "medium":
        return "构图9.1/光影9.2/透视9.0/质感9.1/风格9.0"
    if round_num < 2:
        return "构图9.4/光影8.5/透视9.1/质感9.0/风格9.2"  # photocopy-shaped
    return "构图9.2/光影9.7/透视9.2/质感9.4/风格9.3"  # drama


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

    prof = get_converge_scale_profile(
        api,
        recompose_dir=recompose_dir,
        goal=str(bot.get("goal") or ""),
        ref_image=str(bot.get("ref_image") or ""),
        module=str(bot.get("module") or ""),
    )
    # Engine profile wins if higher.
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

    history = []
    decision = "CONTINUE_NEXT_ROUND"
    for r in range(1, min_r + 1):
        dims = _simulate_dims(api, r)
        defects = (
            "冷暖分离不足，闷贴原图"
            if (api == "high" and r == 1)
            else ("远景略糊" if r == 1 else "体积光可再锐")
        )
        if api == "recompose" and r == 1:
            defects = "机位未变，仍偏原俯瞰"
        if api == "recompose" and r >= 2:
            defects = f"已朝向{recompose_dir}，纵深可再清"

        judge = auto_vlm_judge_image(
            "",
            prof,
            round_num=r,
            dims=dims,
            defects=defects,
            next_fix=str(prof.get("best_direction_hint") or "继续叠加"),
            require_image=False,
        )
        parsed = (parse_5d_dims(dims, prof.get("dim_weights")) or {}).get("parsed") or {}
        sc = score_v7(
            api_scale=api,
            prompt_mode=mode,
            dims=parsed,
            metrics={
                "struct": 0.85 if r == 1 else 0.25,
                "contrast": 0.25 if r == 1 else 0.85,
                "cold_warm_separation": 0.2 if r == 1 else 0.8,
                "edge_energy": 0.2 if r == 1 else 0.75,
                "mse": 200.0 if r == 1 else 600.0,
            },
        )
        # Runner must NOT stop solely because scorer ≥ 9.60 on R1.
        engine_passed = bool(judge.get("passed"))
        early = bool(judge.get("early_stop_blocked"))
        decision = str(judge.get("decision") or "")
        history.append(
            {
                "round": r,
                "engine_score": judge.get("calibrated_score"),
                "scorer_score": sc["score"],
                "struct_weight": sc["struct_weight"],
                "lifted_by_struct_floor": sc["lifted_by_struct_floor"],
                "early_stop_blocked": early,
                "decision": decision,
                "engine_passed": engine_passed,
            }
        )
        if engine_passed and r >= min_r:
            break
        if r < min_r and decision == "STOP_TARGET_REACHED":
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": "min_rounds",
                "issues": [f"engine tried STOP at R{r} but min_rounds={min_r}"],
                "history": history,
            }

    # high/recompose must have run ≥2 rounds in this dry path
    if api in ("high", "recompose") and len(history) < 2:
        return {
            "bot_id": bot["bot_id"],
            "ok": False,
            "phase": "min_rounds",
            "issues": [f"only {len(history)} rounds; need ≥2"],
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
        "history": history,
        "final_decision": decision,
    }


def main() -> int:
    tasks = _load_json("bot_tasks_v7.json")
    best = _load_json("best_prompts_by_scale.json")
    bots = tasks.get("bots") or []
    failed = []
    print(f"V7 dry-run · {len(bots)} bots · skills_kit={REPO_ROOT / 'skills_kit'}")
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
