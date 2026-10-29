#!/usr/bin/env python3
"""V7 live 32-bot runner: cold-start converge start→generate→judge + v7_image_scorer.

Expects images already in IMAGES_ROOT/generated_v7/ (final names from gen_jobs.json).
For high/recompose, also accepts optional *_r1.jpg intermediates; if missing, R1 reuses final
but engine still enforces min_rounds≥2 (no R1 scorer-only STOP).

Usage:
  cd /Users/yanghu/Desktop/pmem-art
  PYTHONPATH=. python3 scripts/run_32bots_v7_live.py
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(SCRIPTS))

IMAGES_ROOT = Path(os.environ.get("PMEM_ART_IMAGES_ROOT", "/Users/yanghu/Desktop/pmem-art-images"))
GEN_DIR = IMAGES_ROOT / "generated_v7"
BOTS_ROOT = IMAGES_ROOT / "empty_bots_v7"
REPORT_PATH = IMAGES_ROOT / "empty_bots_v7_32_report.json"
JOBS_PATH = GEN_DIR / "gen_jobs.json"

from skills_kit import (  # noqa: E402
    compose_style_first_prompt,
    find_affirmative_lock_hits,
    get_converge_scale_profile,
    strip_affirmative_locks_from_prompt,
)
from skills_kit.converge import (  # noqa: E402
    converge_finish,
    converge_generate,
    converge_judge,
    converge_start,
)
import pmem_art as pa  # noqa: E402
from v7_image_scorer import score_image_v7  # noqa: E402


def _best_overlay(best_doc: dict, bot: dict) -> str:
    if (bot.get("prompt_mode") or "none") != "best":
        return ""
    api = bot.get("api_scale") or "medium"
    case = bot.get("case_id") or ""
    by = (best_doc.get("by_scale") or {}).get(api) or {}
    return str(by.get(case) or by.get("_default") or "")


def _resolve_round_image(bot: dict, round_num: int, min_r: int, final_name: str) -> Path:
    stem = f"{bot['bot_id']}_{bot['slug']}_{bot['display_scale']}"
    if round_num < min_r:
        cand = GEN_DIR / f"{stem}_r{round_num}.jpg"
        if cand.is_file():
            return cand
        # png fallback
        cand = GEN_DIR / f"{stem}_r{round_num}.png"
        if cand.is_file():
            return cand
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        p = GEN_DIR / f"{Path(final_name).stem}{ext}"
        if p.is_file():
            return p
    # final_name as given
    p = GEN_DIR / final_name
    if p.is_file():
        return p
    raise FileNotFoundError(f"missing image for {bot['bot_id']} R{round_num}: {final_name}")


def run_bot(bot_task: dict, best_doc: dict, job: dict) -> dict:
    bot_id = bot_task["bot_id"]
    api = bot_task["api_scale"]
    mode = bot_task.get("prompt_mode") or "none"
    recompose_dir = bot_task.get("recompose_dir") or ""
    min_r = int(job.get("min_rounds") or bot_task.get("min_rounds_before_stop") or 1)
    display = bot_task["display_scale"]
    bot_root = BOTS_ROOT / f"{bot_id}_{bot_task['slug']}_{display}"
    if bot_root.exists():
        shutil.rmtree(bot_root)
    bot_root.mkdir(parents=True, exist_ok=True)

    bot_home = bot_root / "home"
    (bot_home / ".claude").mkdir(parents=True, exist_ok=True)
    (bot_home / ".cache").mkdir(parents=True, exist_ok=True)
    shared_root = bot_root / "empty_shared_memory"
    shared_root.mkdir(parents=True, exist_ok=True)

    # Install Desktop modular package pieces (not box monolithic skills_kit.py)
    for name in ("pmem_art.py", "lifecycle.py", "classify.py", "feedback.py", "vlm_judge.py"):
        src = REPO_ROOT / name
        if src.is_file():
            shutil.copy2(src, bot_root / name)
    # copy skills_kit + improve packages
    sk_dst = bot_root / "skills_kit"
    if sk_dst.exists():
        shutil.rmtree(sk_dst)
    shutil.copytree(REPO_ROOT / "skills_kit", sk_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    imp_dst = bot_root / "improve"
    if imp_dst.exists():
        shutil.rmtree(imp_dst)
    if (REPO_ROOT / "improve").is_dir():
        shutil.copytree(REPO_ROOT / "improve", imp_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    refs_dir = bot_root / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    ref_src = REPO_ROOT / bot_task["ref_image"]
    ref_dst = refs_dir / Path(bot_task["ref_image"]).name
    shutil.copy2(ref_src, ref_dst)

    out_dir = bot_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    os.environ["HOME"] = str(bot_home)
    os.environ["PMEM_ART_SHARED_ROOT"] = str(shared_root)

    # fresh import context: ensure bot_root on path
    if str(bot_root) not in sys.path:
        sys.path.insert(0, str(bot_root))

    mem_dir = bot_root / ".memory-art"
    (mem_dir / "entries").mkdir(parents=True, exist_ok=True)
    (mem_dir / "converge").mkdir(parents=True, exist_ok=True)
    (mem_dir / "config.yaml").write_text(
        "project:\n"
        f"  name: {bot_id}_{bot_task['slug']}_{display}\n"
        "style: v7\n"
        "version: 1.0\n",
        encoding="utf-8",
    )

    cold = {
        "isolated_home": str(bot_home),
        "old_memories_loaded": len(list(mem_dir.rglob("entries/**/*.md"))),
        "old_cache_entries": len(list((bot_home / ".cache").rglob("*"))),
        "old_converge_records": len(list((mem_dir / "converge").glob("*.json"))),
    }
    assert cold["old_memories_loaded"] == 0
    assert cold["old_cache_entries"] == 0
    assert cold["old_converge_records"] == 0

    data = pa.load_project(bot_root)
    session_id = f"v7_{bot_id}_{display}"
    threshold = 9.60

    start_res = converge_start(
        bot_root,
        data,
        session_id=session_id,
        goal=bot_task["goal"],
        module=bot_task.get("module") or "",
        ref_image=str(ref_dst),
        ref_analysis=f"{bot_task['case_id']} {bot_task['slug']}",
        aspect_ratio=bot_task.get("aspect_ratio") or "",
        reference_image_paths=[str(ref_dst)],
        threshold=threshold,
        max_rounds=8,
        scale=api,
        recompose_dir=recompose_dir,
        silent=True,
    )
    if start_res.get("exit_code") != 0:
        return {"bot_id": bot_id, "ok": False, "phase": "start", "start": start_res}

    history = []
    final_img = None
    final_score = None
    decision = ""
    for r in range(1, min_r + 1):
        img_src = _resolve_round_image(bot_task, r, min_r, job["final_filename"])
        gen_dst = out_dir / img_src.name
        shutil.copy2(img_src, gen_dst)
        final_img = gen_dst

        scored = score_image_v7(str(gen_dst), str(ref_dst), api_scale=api, prompt_mode=mode)
        dims_str = scored["dims_str"]
        live_score = scored["score"]
        final_score = live_score

        # prompts from job rounds
        prompt = job["rounds"][min(r - 1, len(job["rounds"]) - 1)]["prompt"]
        prompt = strip_affirmative_locks_from_prompt(prompt, scale=api)
        locks = find_affirmative_lock_hits(prompt)

        gen_res = converge_generate(
            bot_root,
            data,
            session_id=session_id,
            round_num=r,
            prompt=prompt,
            image=str(gen_dst),
            scale=api,
            recompose_dir=recompose_dir,
            aspect_ratio=bot_task.get("aspect_ratio") or "",
            reference_image_paths=[str(ref_dst)],
            goal=bot_task["goal"],
            module=bot_task.get("module") or "",
            ref_image=str(ref_dst),
            ref_analysis=f"{bot_task['case_id']} {bot_task['slug']}",
            threshold=threshold,
            max_rounds=8,
            silent=True,
        )
        if gen_res.get("exit_code") != 0:
            return {"bot_id": bot_id, "ok": False, "phase": f"generate_r{r}", "gen": gen_res}

        defects = []
        if api == "high" and r == 1 and live_score < 9.7:
            defects.append("光影张力不足或偏闷贴")
        if api == "recompose" and r == 1:
            defects.append("机位仍偏原构图，需强化新机位")
        if not defects:
            defects.append("细节可再锐")
        next_fix = str(get_converge_scale_profile(api, recompose_dir=recompose_dir).get("best_direction_hint") or "继续叠加")

        judge_res = converge_judge(
            bot_root,
            data,
            session_id=session_id,
            round_num=r,
            image=str(gen_dst),
            dims=dims_str,
            strengths="v7 live pixel score",
            defects="；".join(defects),
            next_fix=next_fix,
            scale=api,
            recompose_dir=recompose_dir,
            threshold=threshold,
            max_rounds=8,
            silent=True,
        )
        if judge_res.get("exit_code") != 0:
            return {"bot_id": bot_id, "ok": False, "phase": f"judge_r{r}", "judge": judge_res}

        judged = judge_res.get("round") or {}
        decision = str(judged.get("decision") or "")
        early = bool(judged.get("early_stop_blocked"))
        # Hard rule: never accept STOP before min_rounds for high/recompose
        if decision == "STOP_TARGET_REACHED" and r < min_r:
            # treat as blocked early stop
            early = True
            decision = "CONTINUE_NEXT_ROUND"

        history.append(
            {
                "round": r,
                "image": str(gen_dst),
                "score": live_score,
                "dims": scored["dims"],
                "metrics": scored["metrics"],
                "struct_weight": scored["struct_weight"],
                "lifted_by_struct_floor": scored["lifted_by_struct_floor"],
                "decision": decision,
                "early_stop_blocked": early,
                "lock_hits": locks,
                "md5_12": hashlib.md5(gen_dst.read_bytes()).hexdigest()[:12],
            }
        )

        if decision == "STOP_TARGET_REACHED" and r >= min_r:
            break
        # If engine passed but we still need rounds, continue
        if r >= min_r and live_score >= threshold:
            decision = "STOP_TARGET_REACHED"
            break

    finish_res = converge_finish(bot_root, data, session_id=session_id, apply_memory=True, silent=True)

    # param validation from session
    session_path = mem_dir / "converge" / f"{session_id}.json"
    saved = json.loads(session_path.read_text(encoding="utf-8")) if session_path.is_file() else {}
    pv = {}
    if saved.get("rounds"):
        pv = saved["rounds"][-1].get("param_validation") or saved.get("param_validation") or {}

    rounds_executed = len(history)
    ok = (
        cold["old_memories_loaded"] == 0
        and rounds_executed >= min_r
        and all(not h.get("lock_hits") for h in history)
        and not any(h.get("lifted_by_struct_floor") for h in history)
        and (api not in ("high", "recompose") or rounds_executed >= 2)
        and finish_res.get("exit_code") == 0
    )
    # PASS bar: final score >= 9.60 preferred but report honestly
    passed_score = bool(final_score is not None and final_score >= threshold)

    return {
        "bot_id": bot_id,
        "ok": ok,
        "passed_score": passed_score,
        "acceptance_passed": ok and passed_score,
        "case_id": bot_task["case_id"],
        "slug": bot_task["slug"],
        "display_scale": display,
        "api_scale": api,
        "prompt_mode": mode,
        "aspect_ratio": bot_task.get("aspect_ratio"),
        "min_rounds": min_r,
        "rounds_executed": rounds_executed,
        "final_score": final_score,
        "final_image": str(final_img) if final_img else None,
        "final_filename": job["final_filename"],
        "decision": decision,
        "history": history,
        "param_validation": pv,
        "cold_start_audit": cold,
        "pipeline_mode": saved.get("pipeline_mode"),
        "finish_exit": finish_res.get("exit_code"),
    }


def main() -> int:
    tasks = json.loads((REPO_ROOT / "bot_tasks_v7.json").read_text(encoding="utf-8"))
    best = json.loads((REPO_ROOT / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    jobs_doc = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    jobs_by_id = {j["bot_id"]: j for j in jobs_doc["jobs"]}
    BOTS_ROOT.mkdir(parents=True, exist_ok=True)

    results = []
    failed = []
    print(f"V7 LIVE · {len(tasks['bots'])} bots · GEN={GEN_DIR}")
    print(f"skills_kit={REPO_ROOT / 'skills_kit'}")
    for bot in tasks["bots"]:
        job = jobs_by_id[bot["bot_id"]]
        try:
            res = run_bot(bot, best, job)
        except Exception as e:
            res = {"bot_id": bot["bot_id"], "ok": False, "phase": "exception", "error": str(e)}
        results.append(res)
        mark = "PASS" if res.get("acceptance_passed") else ("OK_LOWSCORE" if res.get("ok") else "FAIL")
        print(
            f"[{mark}] {res.get('bot_id')} {bot.get('display_scale')} "
            f"score={res.get('final_score')} rounds={res.get('rounds_executed')} "
            f"min_r={res.get('min_rounds')}"
        )
        if not res.get("ok"):
            failed.append(res)
            if res.get("error"):
                print("      ·", res["error"])
            if res.get("phase"):
                print("      · phase", res["phase"])

    report = {
        "version": "v7",
        "n_bots": len(results),
        "n_ok": sum(1 for r in results if r.get("ok")),
        "n_pass_score": sum(1 for r in results if r.get("passed_score")),
        "n_acceptance": sum(1 for r in results if r.get("acceptance_passed")),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport → {REPORT_PATH}")
    print(
        f"Summary: ok={report['n_ok']}/{report['n_bots']} "
        f"score≥9.60={report['n_pass_score']} acceptance={report['n_acceptance']}"
    )
    return 0 if report["n_ok"] == report["n_bots"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
