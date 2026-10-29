#!/usr/bin/env python3
"""V8 live 32-bot runner — Absolute-5D v9.1 checklist offline + Intent/Δ; R2+ prompt reflow.

Modes (must pass one explicitly):
  --score-only   Score existing images only. NEVER calls GenerateImage.
                 Prefers generated_v8/, else remaps v8_bot_* → generated_v7/v7_bot_*.
                 Missing intermediate *_rN for min_rounds≥2 → FAIL (no final-image reuse).
                 Report is NOT proof that V8 prompts beat V2.
  --converge     Isolated converge start/generate/judge using on-disk round images
                 (still no GenerateImage API — images must already exist).

Batch/diagnostic STOP band = HEURISTIC_STOP_THRESHOLD (8.50) on pixel Absolute-5D only.
Product converge (pmem_art converge judge) stays ≥9.50 via VLM or Agent Absolute-5D;
this script's 8.50 is NOT the skill/converge accept gate.

Usage:
  cd /Users/yanghu/Desktop/pmem-art
  export PYTHONPATH="/Users/yanghu/Desktop/pmem-art${PYTHONPATH:+:$PYTHONPATH}"
  python3 scripts/run_32bots_v8_live.py --score-only --write-html
  python3 scripts/run_32bots_v8_live.py --converge --limit 2
"""
from __future__ import annotations

import argparse
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
GEN_V8 = IMAGES_ROOT / "generated_v8"
GEN_V7 = IMAGES_ROOT / "generated_v7"
BOTS_ROOT = IMAGES_ROOT / "empty_bots_v8"
REPORT_PATH = IMAGES_ROOT / "empty_bots_v8_32_report.json"
HTML_PATH = IMAGES_ROOT / "pmem_art_images_v8_32bots_showcase.html"

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
from absolute_5d_scorer import (  # noqa: E402
    HEURISTIC_STOP_THRESHOLD,
    LEGACY_SHOWCASE_STOP,
    absolute_5d,
    intent_check,
    rewrite_prompt_from_defects,
    score_pair,
)


def _best_overlay(best_doc: dict, bot: dict) -> str:
    mode = bot.get("prompt_mode") or "none"
    if mode == "style_jump":
        by = (best_doc.get("by_scale") or {}).get("recompose_bold") or {}
        return str(by.get(bot.get("case_id") or "") or by.get("_default") or "")
    if mode != "best":
        return ""
    api = bot.get("api_scale") or "medium"
    by = (best_doc.get("by_scale") or {}).get(api) or {}
    return str(by.get(bot.get("case_id") or "") or by.get("_default") or "")


def _resolve_image(bot: dict, round_num: int, min_r: int, *, allow_final_fallback: bool = False) -> Path | None:
    """Resolve round image. Prefer generated_v8; else remap to generated_v7.

    For rounds before the final (round_num < min_r): ONLY accept *_rN files.
    Never silently reuse the final image to fake multi-round (unless allow_final_fallback).
    """
    stem = f"{bot['bot_id']}_{bot['slug']}_{bot['display_scale']}"
    v7_stem = stem.replace("v8_", "v7_")
    candidates: list[Path] = []
    if round_num < min_r:
        for root, st in ((GEN_V8, stem), (GEN_V7, v7_stem)):
            for ext in (".jpg", ".jpeg", ".png", ".webp"):
                candidates.append(root / f"{st}_r{round_num}{ext}")
        if not allow_final_fallback:
            for c in candidates:
                if c.is_file():
                    return c
            return None
    for root, st in ((GEN_V8, stem), (GEN_V7, v7_stem)):
        for ext in (".jpg", ".jpeg", ".png", ".webp"):
            candidates.append(root / f"{st}{ext}")
    for c in candidates:
        if c.is_file():
            return c
    return None


def _compose_prompt(bot: dict, best_doc: dict, round_num: int, defects: list[str], intent: dict | None) -> str:
    api = bot["api_scale"]
    mode = bot.get("prompt_mode") or "none"
    recompose_dir = bot.get("recompose_dir") or ""
    prof = get_converge_scale_profile(
        api,
        recompose_dir=recompose_dir,
        goal=bot.get("goal") or "",
        ref_image=bot.get("ref_image") or "",
        module=bot.get("module") or "",
    )
    base = " | ".join(
        x for x in (bot.get("gen_description"), bot.get("goal"), _best_overlay(best_doc, bot)) if x
    )
    base = strip_affirmative_locks_from_prompt(base, scale=api)
    composed = compose_style_first_prompt(base, prof)
    if round_num >= 2:
        composed = rewrite_prompt_from_defects(
            composed,
            defects=defects or ["继续强化档位意图"],
            intent=intent,
            api_scale=api,
            recompose_dir=recompose_dir,
        )
    return composed


def score_only_bot(bot: dict, best_doc: dict, baselines: dict[str, dict]) -> dict:
    api = bot["api_scale"]
    mode = bot.get("prompt_mode") or "none"
    recompose_dir = bot.get("recompose_dir") or ""
    min_r = int(bot.get("min_rounds_before_stop") or 1)
    if mode == "style_jump" or api in ("high", "recompose"):
        min_r = max(min_r, 2)
    threshold = HEURISTIC_STOP_THRESHOLD

    ref_src = REPO_ROOT / bot["ref_image"]
    if not ref_src.is_file():
        return {"bot_id": bot["bot_id"], "ok": False, "phase": "ref_missing", "error": str(ref_src)}

    case_key = bot["slug"]
    if case_key not in baselines:
        baselines[case_key] = absolute_5d(str(ref_src), api_scale=api, prompt_mode=mode)

    history = []
    final_score = None
    final_img = None
    decision = "CONTINUE_NEXT_ROUND"
    intent_last = None
    prompt_last = ""

    for r in range(1, min_r + 1):
        img = _resolve_image(bot, r, min_r, allow_final_fallback=False)
        if img is None:
            return {
                "bot_id": bot["bot_id"],
                "ok": False,
                "phase": f"image_r{r}",
                "error": (
                    f"missing round image R{r} (need *_r{r}.* when min_rounds={min_r}; "
                    "refusing to reuse final — no fake multi-round)"
                ),
            }
        final_img = img
        pair = score_pair(
            str(img),
            str(ref_src),
            api_scale=api,
            prompt_mode=mode,
            recompose_dir=recompose_dir,
        )
        # Prefer case baseline scored once at the bot's scale for Δ display consistency
        # but Absolute-5D baseline for the case uses same function on ref.
        baseline = baselines[case_key]
        # Re-score baseline at this bot's scale for fair Δ
        baseline_scaled = absolute_5d(str(ref_src), api_scale=api, prompt_mode=mode)
        delta = round(float(pair["score"]) - float(baseline_scaled["score"]), 2)
        intent = intent_check(
            api_scale=api,
            prompt_mode=mode,
            bot_score=pair["bot"],
            baseline_score=baseline_scaled,
            recompose_dir=recompose_dir,
        )
        intent_last = intent
        defects = []
        if not intent.get("pass"):
            defects.append(str(intent.get("reason") or "intent fail"))
        if pair["score"] < threshold:
            defects.append(f"Absolute-5D {pair['score']} < {threshold}")
        prompt_last = _compose_prompt(bot, best_doc, r, defects, intent)
        locks = find_affirmative_lock_hits(prompt_last)
        final_score = pair["score"]
        decision = (
            "STOP_TARGET_REACHED"
            if (pair["score"] >= threshold and r >= min_r and intent.get("pass"))
            else "CONTINUE_NEXT_ROUND"
        )
        if r < min_r:
            decision = "CONTINUE_NEXT_ROUND"
        history.append(
            {
                "round": r,
                "image": str(img),
                "score": pair["score"],
                "baseline_score": baseline_scaled["score"],
                "delta": delta,
                "dims": pair["dims"],
                "metrics": pair["metrics"],
                "vs_ref": pair["vs_ref"],
                "intent": intent,
                "prompt": prompt_last,
                "prompt_rewritten": "【回流修正】" in prompt_last,
                "decision": decision,
                "lock_hits": locks,
                "md5_12": hashlib.md5(img.read_bytes()).hexdigest()[:12],
                "struct_weight": 0.0,
                "lifted_by_struct_floor": False,
            }
        )

    rounds_executed = len(history)
    ok = (
        rounds_executed >= min_r
        and all(not h.get("lock_hits") for h in history)
        and (api not in ("high", "recompose") or rounds_executed >= 2)
    )
    if api in ("high", "recompose") and rounds_executed >= 2:
        ok = ok and any(h.get("prompt_rewritten") for h in history[1:])

    passed_score = bool(final_score is not None and final_score >= threshold)
    return {
        "bot_id": bot["bot_id"],
        "ok": ok,
        "passed_score": passed_score,
        "acceptance_passed": ok and passed_score,
        "case_id": bot["case_id"],
        "slug": bot["slug"],
        "display_scale": bot["display_scale"],
        "api_scale": api,
        "prompt_mode": mode,
        "aspect_ratio": bot.get("aspect_ratio"),
        "min_rounds": min_r,
        "rounds_executed": rounds_executed,
        "final_score": final_score,
        "baseline_score": history[-1]["baseline_score"] if history else None,
        "delta": history[-1]["delta"] if history else None,
        "intent": intent_last,
        "final_image": str(final_img) if final_img else None,
        "final_filename": final_img.name if final_img else None,
        "decision": decision,
        "history": history,
        "scoring_track": "A_absolute_5d_v9_checklist_offline",
        "heuristic_stop": threshold,
        "legacy_showcase_stop": LEGACY_SHOWCASE_STOP,
        "v2_scripted_note": "旧 V2 showcase 分为 scripted，不可与 Absolute-5D 横比",
        "not_v8_generation_proof": True,
        "pipeline_mode": "score_only",
    }


def run_converge_bot(bot: dict, best_doc: dict) -> dict:
    """Isolated converge path using Absolute-5D dims for judge (images must exist)."""
    bot_id = bot["bot_id"]
    api = bot["api_scale"]
    mode = bot.get("prompt_mode") or "none"
    recompose_dir = bot.get("recompose_dir") or ""
    min_r = int(bot.get("min_rounds_before_stop") or 1)
    if mode == "style_jump" or api in ("high", "recompose"):
        min_r = max(min_r, 2)
    display = bot["display_scale"]
    # Product converge gate (same as skills / pmem_art converge), not pixel 8.50 band.
    threshold = LEGACY_SHOWCASE_STOP

    bot_root = BOTS_ROOT / f"{bot_id}_{bot['slug']}_{display}"
    if bot_root.exists():
        shutil.rmtree(bot_root)
    bot_root.mkdir(parents=True, exist_ok=True)
    bot_home = bot_root / "home"
    (bot_home / ".claude").mkdir(parents=True, exist_ok=True)
    (bot_home / ".cache").mkdir(parents=True, exist_ok=True)
    shared_root = bot_root / "empty_shared_memory"
    shared_root.mkdir(parents=True, exist_ok=True)

    for name in ("pmem_art.py", "lifecycle.py", "classify.py", "feedback.py", "vlm_judge.py"):
        src = REPO_ROOT / name
        if src.is_file():
            shutil.copy2(src, bot_root / name)
    sk_dst = bot_root / "skills_kit"
    if sk_dst.exists():
        shutil.rmtree(sk_dst)
    shutil.copytree(REPO_ROOT / "skills_kit", sk_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    if (REPO_ROOT / "improve").is_dir():
        imp_dst = bot_root / "improve"
        if imp_dst.exists():
            shutil.rmtree(imp_dst)
        shutil.copytree(REPO_ROOT / "improve", imp_dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    refs_dir = bot_root / "references"
    refs_dir.mkdir(parents=True, exist_ok=True)
    ref_src = REPO_ROOT / bot["ref_image"]
    ref_dst = refs_dir / Path(bot["ref_image"]).name
    shutil.copy2(ref_src, ref_dst)
    out_dir = bot_root / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    os.environ["HOME"] = str(bot_home)
    os.environ["PMEM_ART_SHARED_ROOT"] = str(shared_root)
    if str(bot_root) not in sys.path:
        sys.path.insert(0, str(bot_root))

    mem_dir = bot_root / ".memory-art"
    (mem_dir / "entries").mkdir(parents=True, exist_ok=True)
    (mem_dir / "converge").mkdir(parents=True, exist_ok=True)
    (mem_dir / "config.yaml").write_text(
        f"project:\n  name: {bot_id}_{bot['slug']}_{display}\nstyle: v8\nversion: 1.0\n",
        encoding="utf-8",
    )

    data = pa.load_project(bot_root)
    session_id = f"v8_{bot_id}_{display}"
    start_res = converge_start(
        bot_root,
        data,
        session_id=session_id,
        goal=bot["goal"],
        module=bot.get("module") or "",
        ref_image=str(ref_dst),
        ref_analysis=f"{bot['case_id']} {bot['slug']}",
        aspect_ratio=bot.get("aspect_ratio") or "",
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
    intent_last = None
    baseline_scaled = absolute_5d(str(ref_dst), api_scale=api, prompt_mode=mode)

    for r in range(1, min_r + 1):
        img_src = _resolve_image(bot, r, min_r, allow_final_fallback=False)
        if img_src is None:
            return {
                "bot_id": bot_id,
                "ok": False,
                "phase": f"image_r{r}",
                "error": (
                    f"missing round image R{r} (need *_r{r}.* when min_rounds={min_r}; "
                    "refusing to reuse final — no fake multi-round)"
                ),
            }
        gen_dst = out_dir / img_src.name
        shutil.copy2(img_src, gen_dst)
        final_img = gen_dst

        pair = score_pair(
            str(gen_dst),
            str(ref_dst),
            api_scale=api,
            prompt_mode=mode,
            recompose_dir=recompose_dir,
        )
        intent = intent_check(
            api_scale=api,
            prompt_mode=mode,
            bot_score=pair["bot"],
            baseline_score=baseline_scaled,
            recompose_dir=recompose_dir,
        )
        intent_last = intent
        defects = []
        if not intent.get("pass"):
            defects.append(str(intent.get("reason") or "intent fail"))
        if pair["score"] < threshold:
            defects.append(f"Absolute-5D {pair['score']} < {threshold}")
        if not defects:
            defects.append("细节可再锐")
        prompt = _compose_prompt(bot, best_doc, r, defects, intent)
        locks = find_affirmative_lock_hits(prompt)
        live_score = pair["score"]
        final_score = live_score
        delta = round(live_score - float(baseline_scaled["score"]), 2)

        gen_res = converge_generate(
            bot_root,
            data,
            session_id=session_id,
            round_num=r,
            prompt=prompt,
            image=str(gen_dst),
            scale=api,
            recompose_dir=recompose_dir,
            aspect_ratio=bot.get("aspect_ratio") or "",
            reference_image_paths=[str(ref_dst)],
            goal=bot["goal"],
            module=bot.get("module") or "",
            ref_image=str(ref_dst),
            ref_analysis=f"{bot['case_id']} {bot['slug']}",
            threshold=threshold,
            max_rounds=8,
            silent=True,
        )
        if gen_res.get("exit_code") != 0:
            return {"bot_id": bot_id, "ok": False, "phase": f"generate_r{r}", "gen": gen_res}

        next_fix = str(get_converge_scale_profile(api, recompose_dir=recompose_dir).get("best_direction_hint") or "继续叠加")
        # Batch-only: inject offline Absolute-5D dims as CLI stand-in (no vision Agent in CI).
        # Product skills never do this — Agent/VLM owns dims; pixel stays advisory in judge_auto.
        judge_res = converge_judge(
            bot_root,
            data,
            session_id=session_id,
            round_num=r,
            image=str(gen_dst),
            dims=pair["dims_str"],
            strengths=f"batch-offline-inject Absolute-5D {live_score} Δ={delta:+.2f}",
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
        if decision == "STOP_TARGET_REACHED" and r < min_r:
            early = True
            decision = "CONTINUE_NEXT_ROUND"

        history.append(
            {
                "round": r,
                "image": str(gen_dst),
                "score": live_score,
                "baseline_score": baseline_scaled["score"],
                "delta": delta,
                "dims": pair["dims"],
                "metrics": pair["metrics"],
                "vs_ref": pair["vs_ref"],
                "intent": intent,
                "prompt": prompt,
                "prompt_rewritten": "【回流修正】" in prompt,
                "decision": decision,
                "early_stop_blocked": early,
                "lock_hits": locks,
                "md5_12": hashlib.md5(gen_dst.read_bytes()).hexdigest()[:12],
                "struct_weight": 0.0,
                "lifted_by_struct_floor": False,
            }
        )
        if decision == "STOP_TARGET_REACHED" and r >= min_r:
            break
        # Do not override judge CONTINUE with Absolute-5D pair score alone —
        # stop must come from converge/judge (VLM or offline_checklist_5d).

    finish_res = converge_finish(bot_root, data, session_id=session_id, apply_memory=True, silent=True)
    rounds_executed = len(history)
    ok = (
        rounds_executed >= min_r
        and all(not h.get("lock_hits") for h in history)
        and finish_res.get("exit_code") == 0
        and (api not in ("high", "recompose") or rounds_executed >= 2)
    )
    passed_score = bool(final_score is not None and final_score >= threshold)
    return {
        "bot_id": bot_id,
        "ok": ok,
        "passed_score": passed_score,
        "acceptance_passed": ok and passed_score,
        "case_id": bot["case_id"],
        "slug": bot["slug"],
        "display_scale": display,
        "api_scale": api,
        "prompt_mode": mode,
        "aspect_ratio": bot.get("aspect_ratio"),
        "min_rounds": min_r,
        "rounds_executed": rounds_executed,
        "final_score": final_score,
        "baseline_score": baseline_scaled["score"],
        "delta": history[-1]["delta"] if history else None,
        "intent": intent_last,
        "final_image": str(final_img) if final_img else None,
        "final_filename": final_img.name if final_img else None,
        "decision": decision,
        "history": history,
        "scoring_track": "A_absolute_5d_v9_checklist_offline",
        "heuristic_stop": threshold,
        "legacy_showcase_stop": LEGACY_SHOWCASE_STOP,
        "v2_scripted_note": "旧 V2 showcase 分为 scripted，不可与 Absolute-5D 横比",
        "not_v8_generation_proof": True,
        "pipeline_mode": "converge",
        "finish_exit": finish_res.get("exit_code"),
    }


def build_html(report: dict, tasks: dict) -> str:
    """Compact V8 showcase: Absolute-5D + Δ + Intent; V2 scripted disclaimer."""
    by_slug: dict[str, list] = {}
    for r in report.get("results") or []:
        by_slug.setdefault(r.get("slug") or "?", []).append(r)
    ref_by_slug = {}
    for b in tasks.get("bots") or []:
        ref_by_slug[b["slug"]] = b["ref_image"]

    sections = []
    for slug, group in by_slug.items():
        bas = next((g.get("baseline_score") for g in group if g.get("baseline_score") is not None), None)
        cards = []
        # baseline card
        ref_rel = ref_by_slug.get(slug, "")
        cards.append(
            f"""<div class="col-card ref-card">
  <div class="source-tag">📥 起点 · 原图 · Absolute-5D Baseline</div>
  <div class="img-wrap"><img src="../pmem-art/{ref_rel}" alt="{slug}" loading="lazy"
    onerror="this.src='generated_v7/{Path(ref_rel).name}'"></div>
  <div class="score-line"><span class="score-pill">Baseline <strong>{bas if bas is not None else '—'}</strong></div>
  <div class="dims-line">同尺 Absolute-5D（非 (ref,ref)+low struct）</div>
</div>"""
        )
        for g in sorted(group, key=lambda x: x.get("bot_id") or ""):
            intent = g.get("intent") or {}
            ip = "PASS" if intent.get("pass") else "FAIL"
            delta = g.get("delta")
            dlt = f"{delta:+.2f}" if isinstance(delta, (int, float)) else "—"
            img = g.get("final_filename") or ""
            cards.append(
                f"""<div class="col-card">
  <div class="source-tag">{g.get('bot_id')} · {g.get('display_scale')}</div>
  <div class="img-wrap"><img src="generated_v7/{img.replace('v8_','v7_')}" alt="{img}" loading="lazy"
    onerror="this.src='generated_v8/{img}'"></div>
  <div class="score-line">
    <span class="score-pill">A <strong>{g.get('final_score')}</strong></span>
    <span class="score-pill">Δ {dlt}</span>
    <span class="score-pill">Intent {ip}</span>
  </div>
  <div class="dims-line">{(intent.get('reason') or '')[:80]}</div>
</div>"""
            )
        sections.append(
            f"""<section class="case-block">
  <div class="case-header"><h2>{slug}</h2>
  <div class="case-meta">Absolute-5D Baseline <strong>{bas}</strong> · V2 剧本分不可横比</div></div>
  <div class="grid">{''.join(cards)}</div>
</section>"""
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<title>pmem-art V8 · Absolute-5D · 32 Bot</title>
<style>
body{{background:#0b0f19;color:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,sans-serif;padding:24px}}
header{{background:#111827;border:1px solid #312e81;border-radius:16px;padding:20px;margin-bottom:24px}}
.case-block{{background:#111827;border:1px solid #1e293b;border-radius:16px;padding:16px;margin-bottom:24px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}}
.col-card{{background:#0f172a;border:1px solid #1e293b;border-radius:12px;padding:10px}}
.ref-card{{border-top:3px solid #64748b}}
.img-wrap{{aspect-ratio:3/4;background:#020617;border-radius:8px;overflow:hidden}}
.img-wrap img{{width:100%;height:100%;object-fit:contain}}
.score-pill{{font-size:11px;background:#1e293b;padding:2px 8px;border-radius:6px;margin-right:4px}}
.dims-line{{font-size:11px;color:#94a3b8;margin-top:6px}}
.source-tag{{font-size:11px;margin-bottom:6px}}
.case-meta{{font-size:12px;color:#94a3b8}}
</style></head><body>
<header>
<h1>pmem-art V8 · Absolute-5D v9.1 checklist · Intent/Δ 辅轨</h1>
<p style="background:#7f1d1d;color:#fecaca;padding:10px 12px;border-radius:8px;margin-bottom:12px">
⚠️ <strong>非 V8 生成证明</strong>：本页若为 <code>score-only</code>，只是对已有图（常为 generated_v7）重打 Absolute-5D，
<strong>不能</strong>证明 V8 提示已追上 V2。无 GenerateImage · 无 fake 多轮复用终图。
</p>
<p>主分 <code>absolute_5d_scorer</code> v9.1 audit-patched checklist；Baseline 同尺。
mode=<strong>{report.get('pipeline_mode')}</strong> ·
score-only 诊断带 STOP=<strong>{HEURISTIC_STOP_THRESHOLD}</strong> ·
converge 产品闸 STOP=<strong>{LEGACY_SHOWCASE_STOP}</strong>
（像素尺不冒充产品闸；有 Key 时产品路径优先 VLM）。
MSE/struct 仅诊断。<strong>旧 V2 showcase 分为 scripted，不可横比。</strong><br>
ok={report.get('n_ok')}/{report.get('n_bots')} ·
≥{LEGACY_SHOWCASE_STOP if report.get('pipeline_mode')=='converge' else HEURISTIC_STOP_THRESHOLD}={report.get('n_pass_score')} ·
mode={report.get('pipeline_mode')}</p>
</header>
{''.join(sections)}
<footer style="color:#64748b;font-size:12px;margin-top:24px">PYTHONPATH → Desktop skills_kit · 先确认后再 GenerateImage 产出 generated_v8/</footer>
</body></html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(
        description="V8 live runner. Must pass --score-only or --converge explicitly."
    )
    mode_g = ap.add_mutually_exclusive_group(required=True)
    mode_g.add_argument(
        "--score-only",
        action="store_true",
        help="Score existing images only; no GenerateImage; not V8 generation proof",
    )
    mode_g.add_argument(
        "--converge",
        action="store_true",
        help="Converge path with on-disk round images (still no GenerateImage API)",
    )
    ap.add_argument("--write-html", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="Optional bot cap for smoke")
    args = ap.parse_args()

    tasks = json.loads((REPO_ROOT / "bot_tasks_v8.json").read_text(encoding="utf-8"))
    best = json.loads((REPO_ROOT / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    bots = list(tasks["bots"])
    if args.limit:
        bots = bots[: args.limit]

    BOTS_ROOT.mkdir(parents=True, exist_ok=True)
    baselines: dict[str, dict] = {}
    results = []
    mode = "score_only" if args.score_only else "converge"
    stop_band = HEURISTIC_STOP_THRESHOLD if mode == "score_only" else LEGACY_SHOWCASE_STOP
    print(
        f"V8 LIVE · {len(bots)} bots · mode={mode} · Absolute-5D v9 · "
        f"STOP={stop_band}"
        + (" (pixel diagnostic)" if mode == "score_only" else " (product converge gate)")
    )
    print(f"skills_kit={REPO_ROOT / 'skills_kit'}")
    print(
        "NOTE: no GenerateImage in either mode; score-only ≠ V8 prompt proof; "
        "missing *_rN fails (no final reuse)."
    )

    for bot in bots:
        try:
            if args.score_only:
                res = score_only_bot(bot, best, baselines)
            else:
                res = run_converge_bot(bot, best)
        except Exception as e:
            res = {"bot_id": bot["bot_id"], "ok": False, "phase": "exception", "error": str(e)}
        results.append(res)
        mark = "PASS" if res.get("acceptance_passed") else ("OK_LOWSCORE" if res.get("ok") else "FAIL")
        intent = res.get("intent") or {}
        print(
            f"[{mark}] {res.get('bot_id')} {bot.get('display_scale')} "
            f"A={res.get('final_score')} Δ={res.get('delta')} "
            f"intent={'P' if intent.get('pass') else 'F'} "
            f"base={res.get('baseline_score')} rounds={res.get('rounds_executed')}"
        )
        if res.get("error"):
            print("      ·", res["error"])

    report = {
        "version": "v9.1_checklist_offline",
        "pipeline_mode": mode,
        "scoring_track": "A_absolute_5d_v9_checklist_offline",
        "heuristic_stop": HEURISTIC_STOP_THRESHOLD,
        "legacy_showcase_stop": LEGACY_SHOWCASE_STOP,
        "active_stop": stop_band,
        "v2_scripted_note": "旧 V2 showcase 分为 scripted，不可与 Absolute-5D 横比",
        "not_v8_generation_proof": True,
        "no_generate_image": True,
        "no_fake_multi_round": True,
        "n_bots": len(results),
        "n_ok": sum(1 for r in results if r.get("ok")),
        "n_pass_score": sum(1 for r in results if r.get("passed_score")),
        "n_acceptance": sum(1 for r in results if r.get("acceptance_passed")),
        "baselines": {k: {"score": v.get("score"), "dims": v.get("dims")} for k, v in baselines.items()},
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nReport → {REPORT_PATH}")
    if args.write_html:
        HTML_PATH.write_text(build_html(report, tasks), encoding="utf-8")
        print(f"HTML → {HTML_PATH}")
    print(
        f"Summary: ok={report['n_ok']}/{report['n_bots']} "
        f"score≥{stop_band}={report['n_pass_score']} "
        f"acceptance={report['n_acceptance']} · NOT V8 generation proof"
    )
    return 0 if report["n_ok"] == report["n_bots"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
