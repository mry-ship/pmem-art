#!/usr/bin/env python3
"""V8-20 skill-contract converge: STOP>=9.60, max 8 rounds, real defect reflow.

Uses skills_kit prompt profiles + gpt-image-2 edits + gpt-6-sol Absolute-5D Quant.
Default pad = style_ref every round (skills_kit-aligned); optional previous/auto.
Output: generated_v8_20_skill/
Never prints API keys.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from skills_kit import (  # noqa: E402
    compose_style_first_prompt,
    find_affirmative_lock_hits,
    get_converge_scale_profile,
    strip_affirmative_locks_from_prompt,
)
from skills_kit.prompt_scale import DEFAULT_MAX_ROUNDS, DEFAULT_THRESHOLD  # noqa: E402

from v8_skill_converge_policy import (  # noqa: E402
    DEFAULT_ANATOMY_FLOOR,
    DEFAULT_AUTO_PAD_DROP,
    DEFAULT_PAD_MODE,
    DEFAULT_PLATEAU_ROUNDS,
    DEFAULT_REGRESSION_DROP,
    PROMPT_CHAR_BUDGET,
    anatomy_score,
    choose_next_pad,
    decide_round_stop,
    pick_best_round_on_stop,
    rewrite_reflow_by_dims,
    should_force_ref_pad,
    truncate_prompt,
)

AR_SIZE = {
    "9:16": "1024x1536",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
    "1:1": "1024x1024",
}
WANT_SCALES = {"low_best", "medium_best", "high_best", "recompose", "recompose_bold"}
REF_FILES = [
    ("style_ref_01_night_city.png", "comparison/style_refs/style_ref_01_night_city.png", "night_city", "9:16"),
    ("style_ref_02_pastel_sketch.png", "comparison/style_refs/style_ref_02_pastel_sketch.png", "pastel_sketch", "4:3"),
    ("style_ref_03_sunlit_portrait.png", "comparison/style_refs/style_ref_03_sunlit_portrait.png", "sunlit_portrait", "3:4"),
    ("web_ref_01_concept_ishtar.png", "comparison/web_refs/web_ref_01_concept_ishtar.png", "ishtar_canyon", "4:3"),
]

_log_lock = threading.Lock()


def log(msg: str) -> None:
    with _log_lock:
        print(msg, flush=True)


def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    for k in ("APIKEY_FAN_BASE", "APIKEY_FAN_KEY"):
        if os.environ.get(k):
            out[k] = os.environ[k]
        if not out.get(k):
            raise SystemExit(f"missing {k}")
    return out


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def best_overlay(best_doc: dict, bot: dict) -> str:
    mode = bot.get("prompt_mode") or "none"
    if mode == "style_jump":
        by = (best_doc.get("by_scale") or {}).get("recompose_bold") or {}
        return str(by.get(bot.get("case_id") or "") or by.get("_default") or "")
    if mode != "best":
        return ""
    api = bot.get("api_scale") or "medium"
    by = (best_doc.get("by_scale") or {}).get(api) or {}
    return str(by.get(bot.get("case_id") or "") or by.get("_default") or "")


def compose_prompt(
    bot: dict,
    best_doc: dict,
    round_num: int = 1,
    defects: list[str] | None = None,
    dims: dict[str, Any] | None = None,
) -> str:
    api = bot["api_scale"]
    mode = bot.get("prompt_mode") or "none"
    recompose_dir = bot.get("recompose_dir") or ""
    ar = bot.get("aspect_ratio") or ""
    base = " | ".join(
        x for x in (bot.get("gen_description"), bot.get("goal"), best_overlay(best_doc, bot)) if x
    )
    base = strip_affirmative_locks_from_prompt(base, scale=api)

    if mode == "style_jump":
        tail = "约束：仅保留主体剪影与画幅比；风格圣经按目标大跳；禁止混装旧机位与保色板套话"
        if ar:
            tail = f"约束：画幅 {ar}；仅保留主体剪影；风格圣经按目标大跳；禁止混装旧机位与保色板套话"
        composed = " | ".join(x for x in (base, tail) if x)
        composed = re.sub(r"(?:约束：)?保持原图画风笔触与色板；?", "", composed)
        composed = re.sub(r"保画风色板，按「[^」]*」重构机位\s*\|\s*", "", composed)
        composed = re.sub(r"\s*\|\s*\|\s*", " | ", composed).strip(" |")
    else:
        prof = get_converge_scale_profile(
            api,
            recompose_dir=recompose_dir,
            goal=bot.get("goal") or "",
            ref_image=bot.get("ref_image") or "",
            module=bot.get("module") or "",
        )
        composed = compose_style_first_prompt(base, prof)

    if round_num >= 2:
        composed = rewrite_reflow_by_dims(
            composed,
            defects=defects or [],
            dims=dims,
            api_scale=api,
            recompose_dir="" if mode == "style_jump" else recompose_dir,
            max_fixes=2,
        )
    return composed


def edit_image(*, env: dict[str, str], model: str, src: Path, prompt: str, size: str, out_path: Path, timeout: int = 240) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        resp_path = Path(tf.name)
    prompt_send = truncate_prompt(prompt, PROMPT_CHAR_BUDGET)
    cmd = [
        "curl", "-sS", "-o", str(resp_path), "-w", "%{http_code}",
        "-H", f"Authorization: Bearer {env['APIKEY_FAN_KEY']}",
        "-F", f"model={model}",
        "-F", f"prompt={prompt_send}",
        "-F", f"image=@{src}",
        "-F", f"size={size}",
        "-F", "response_format=b64_json",
        f"{env['APIKEY_FAN_BASE'].rstrip('/')}/v1/images/edits",
    ]
    t0 = time.time()
    last_err = ""
    for attempt in range(1, 5):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            http = (proc.stdout or "").strip()
            raw = resp_path.read_text(encoding="utf-8", errors="replace")
            if http != "200":
                raise RuntimeError(f"HTTP {http}: {raw[:400]}")
            data = json.loads(raw)
            b64 = (data.get("data") or [{}])[0].get("b64_json")
            if not b64:
                raise RuntimeError(f"no b64_json: {raw[:300]}")
            out_path.write_bytes(base64.b64decode(b64))
            try:
                resp_path.unlink(missing_ok=True)
            except Exception:
                pass
            return {
                "ok": True,
                "path": str(out_path),
                "bytes": out_path.stat().st_size,
                "elapsed": round(time.time() - t0, 1),
                "attempt": attempt,
            }
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            sleep = min(60, 4 * attempt)
            log(f"  retry {attempt}/4 {out_path.name}: {last_err[:160]} (sleep {sleep}s)")
            time.sleep(sleep)
    try:
        resp_path.unlink(missing_ok=True)
    except Exception:
        pass
    return {"ok": False, "error": last_err, "path": str(out_path)}


def score_image(
    *,
    path: Path,
    env: dict[str, str],
    model: str,
    role: str,
    bot: dict | None = None,
    round_num: int | None = None,
    goal: str = "",
) -> dict[str, Any]:
    item = {
        "id": f"{role}::{path.name}" + (f"::r{round_num}" if round_num else ""),
        "filename": path.name,
        "path": str(path),
        "sha256": sha256_file(path),
        "role": role,
        "bot_id": (bot or {}).get("bot_id") or "",
        "slug": (bot or {}).get("slug") or "",
        "api_scale": (bot or {}).get("api_scale") or "medium",
        "display_scale": (bot or {}).get("display_scale") or role,
        "prompt_mode": (bot or {}).get("prompt_mode") or "",
        "round": round_num,
        "goal": goal or (bot or {}).get("goal") or "",
    }
    # Lazy import: helpers stay importable when scorer module is only on the bot host.
    import vlm_quant_5d_scorer as vlm  # noqa: E402
    from skills_kit import get_converge_scale_profile
    from skills_kit.converge_judge_bridge import _normalize_vlm_result

    quant = vlm.score_one(item, env, model, max_side=1024)
    if not quant.get("ok"):
        return quant
    scale_prof = get_converge_scale_profile(
        str(item.get("api_scale") or "medium"),
        goal=str(item.get("goal") or ""),
        ref_image=str((bot or {}).get("ref_image") or ""),
    )
    item = {
        **item,
        "scale_prof": scale_prof,
        "module": str((bot or {}).get("module") or ""),
        "ref_image": str((bot or {}).get("ref_image") or ""),
    }
    return _normalize_vlm_result(quant, item, "vlm_quant_5d", {})


def min_rounds_for(bot: dict) -> int:
    mr = bot.get("min_rounds_before_stop")
    if mr is not None:
        return int(mr)
    api = (bot.get("api_scale") or "").lower()
    mode = bot.get("prompt_mode") or ""
    if mode == "style_jump" or api in ("high", "recompose"):
        return 2
    return 1


def select_bots(doc: dict) -> list[dict]:
    return [b for b in doc["bots"] if b.get("display_scale") in WANT_SCALES]


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="/home/box/.config/pmem-art/apikey_fan.env")
    ap.add_argument("--gen-model", default="gpt-image-2")
    ap.add_argument("--score-model", default="gpt-6-sol")
    ap.add_argument("--out-dir", default=str(REPO / "generated_v8_20_skill"))
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--threshold", type=float, default=float(DEFAULT_THRESHOLD))
    ap.add_argument("--max-rounds", type=int, default=int(DEFAULT_MAX_ROUNDS))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--skip-baselines", action="store_true")
    ap.add_argument(
        "--pad",
        choices=("ref", "previous", "auto"),
        default=DEFAULT_PAD_MODE,
        help="Pad image for R2+: ref=style_ref every round (default); previous=old chain; auto=chain only on new highs",
    )
    ap.add_argument("--anatomy-floor", type=float, default=DEFAULT_ANATOMY_FLOOR,
                    help="perspective_anatomy must reach this to STOP_TARGET_REACHED")
    ap.add_argument("--plateau-rounds", type=int, default=DEFAULT_PLATEAU_ROUNDS,
                    help="Stop after N consecutive non-improving scored rounds")
    ap.add_argument("--regression-drop", type=float, default=DEFAULT_REGRESSION_DROP,
                    help="Stop if scored total drops this far below best")
    ap.add_argument("--auto-pad-drop", type=float, default=DEFAULT_AUTO_PAD_DROP,
                    help="In pad=auto, force style_ref if total < best - this")
    args = ap.parse_args()

    env = load_env(Path(args.env))
    doc = json.loads((REPO / "bot_tasks_v8.json").read_text())
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text())
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    bots = select_bots(doc)
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
        bots = [b for b in bots if any(k in b["bot_id"] or k in b["display_scale"] or k in b["slug"] for k in keys)]
    if args.limit:
        bots = bots[: args.limit]

    contract = {
        "version": "v8_20_skill",
        "threshold": args.threshold,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "anatomy_floor": args.anatomy_floor,
        "plateau_rounds": args.plateau_rounds,
        "regression_drop": args.regression_drop,
        "auto_pad_drop": args.auto_pad_drop,
        "source": "skills_kit DEFAULT_THRESHOLD / DEFAULT_MAX_ROUNDS + runner pad/stop/reflow v2",
        "gen_model": args.gen_model,
        "score_model": args.score_model,
        "bot_ids": [b["bot_id"] for b in bots],
        "count": len(bots),
    }
    atomic_write_json(out_dir / "contract.json", contract)
    log(
        f"skill-converge bots={len(bots)} threshold={args.threshold} max_rounds={args.max_rounds} "
        f"pad={args.pad} anatomy_floor={args.anatomy_floor} "
        f"out={out_dir} gen={args.gen_model} score={args.score_model}"
    )

    # copy refs into out dir for offline HTML
    for name, rel, _slug, _ar in REF_FILES:
        src = REPO / rel
        dst = out_dir / name
        if src.is_file() and (args.force or not dst.is_file()):
            shutil.copy2(src, dst)

    scores_path = out_dir / "vlm_scores.json"
    scores = json.loads(scores_path.read_text()) if scores_path.is_file() else {
        "version": "v8_20_skill",
        "model": args.score_model,
        "threshold": args.threshold,
        "images": {},
        "failures": {},
    }

    # baselines
    if not args.skip_baselines:
        for name, rel, slug, _ar in REF_FILES:
            p = out_dir / name
            if not p.is_file():
                p = REPO / rel
            key = f"baseline::{name}"
            if key in scores.get("images", {}) and scores["images"][key].get("ok") and not args.force:
                log(f"skip baseline score {name}")
                continue
            log(f"SCORE baseline {name}")
            rec = score_image(path=p, env=env, model=args.score_model, role="baseline", goal=f"baseline {slug}")
            if rec.get("ok"):
                scores["images"][key] = rec
            else:
                scores["failures"][key] = rec
            atomic_write_json(scores_path, scores)
            log(f"  baseline {name} total={rec.get('total')} ok={rec.get('ok')}")

    # abort if lock hits on R1 prompts
    for b in bots:
        p1 = compose_prompt(b, best, 1)
        hits = find_affirmative_lock_hits(p1)
        if hits:
            log(f"ABORT lock hits {b['bot_id']}: {hits}")
            return 2

    manifest_path = out_dir / "gen_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {
        "version": "v8_20_skill",
        "threshold": args.threshold,
        "max_rounds": args.max_rounds,
        "items": {},
    }

    def run_bot(bot: dict) -> dict[str, Any]:
        bid = bot["bot_id"]
        stem = f"{bid}_{bot['slug']}_{bot['display_scale']}"
        final_path = out_dir / f"{stem}.jpg"
        min_r = min_rounds_for(bot)
        size = AR_SIZE.get(bot.get("aspect_ratio") or "1:1", "1024x1024")
        ref = REPO / bot["ref_image"]
        if not ref.is_file():
            return {"bot_id": bid, "ok": False, "error": f"missing ref {ref}"}

        # resume: if finished manifest and final exists
        prev = manifest.get("items", {}).get(bid) or {}
        if (
            not args.force
            and final_path.is_file()
            and prev.get("ok")
            and prev.get("stop_reason")
            in (
                "STOP_TARGET_REACHED",
                "STOP_PLATEAU",
                "STOP_REGRESSION",
                "max_rounds_reached",
            )
        ):
            log(f"skip done {bid} stop={prev.get('stop_reason')} score={prev.get('final_score')}")
            return prev

        rounds: list[dict[str, Any]] = []
        defects: list[str] = []
        last_ok_dims: dict[str, Any] = {}
        best_round = None
        stop_reason = "max_rounds_reached"
        src = ref
        no_improve_streak = 0
        anatomy_blocked = 0

        for r in range(1, args.max_rounds + 1):
            prompt = compose_prompt(
                bot,
                best,
                r,
                defects=defects if r >= 2 else None,
                dims=last_ok_dims if r >= 2 else None,
            )
            r_path = out_dir / f"{stem}_r{r}.jpg"
            log(f"GEN {bid} R{r}/{args.max_rounds} min_stop={min_r} pad={src.name} -> {r_path.name}")
            gen = edit_image(env=env, model=args.gen_model, src=src, prompt=prompt, size=size, out_path=r_path)
            if not gen.get("ok"):
                return {
                    "bot_id": bid,
                    "ok": False,
                    "phase": f"r{r}",
                    "error": gen.get("error"),
                    "rounds": rounds,
                }

            log(f"SCORE {bid} R{r}")
            scored = score_image(
                path=r_path,
                env=env,
                model=args.score_model,
                role="round" if r < args.max_rounds else "bot",
                bot=bot,
                round_num=r,
                goal=bot.get("goal") or "",
            )
            score_ok = bool(scored.get("ok"))
            total = float(scored.get("total") or 0) if score_ok else None
            dims = scored.get("dims") or {} if score_ok else {}
            round_defects = scored.get("defects") or []
            if isinstance(round_defects, str):
                round_defects = [round_defects]
            if score_ok and not round_defects:
                for k, v in dims.items():
                    try:
                        if float(v) < 8.0:
                            round_defects.append(f"{k}偏低({v})")
                    except Exception:
                        pass
            # Score failure: do NOT invent volume-light defects; keep prior defects/dims

            rec = {
                "round": r,
                "filename": r_path.name,
                "prompt": prompt,
                "pad": src.name,
                "elapsed": gen.get("elapsed"),
                "bytes": gen.get("bytes"),
                "score_ok": score_ok,
                "total": total,
                "dims": dims,
                "defects": (round_defects[:6] if score_ok else list(defects[:6])),
                "grade": scored.get("grade"),
            }
            rounds.append(rec)
            sk = f"round::{stem}::r{r}"
            if score_ok:
                scores["images"][sk] = scored
            else:
                scores["failures"][sk] = scored
            atomic_write_json(scores_path, scores)

            if score_ok and total is not None:
                last_ok_dims = dict(dims)
                if best_round is None or total > float(best_round.get("total") or -1):
                    best_round = rec
                    no_improve_streak = 0
                else:
                    no_improve_streak += 1
                from skills_kit.converge_policy import target_dims_allow_stop
                from skills_kit.prompt_scale import classify_subject

                if (
                    total >= args.threshold
                    and r >= min_r
                    and not target_dims_allow_stop(
                        dims,
                        args.anatomy_floor,
                        subject_kind=classify_subject(
                            goal=str(bot.get("goal") or ""),
                            module=str(bot.get("module") or ""),
                            ref_image=str(bot.get("ref_image") or ""),
                        ),
                        defects="；".join(str(x) for x in (round_defects or [])),
                        style_text=" ".join(
                            str(bot.get(k) or "") for k in ("goal", "module", "ref_image")
                        ),
                    )
                ):
                    anatomy_blocked += 1

            log(
                f"  {bid} R{r} total={total} score_ok={score_ok} "
                f"anat={anatomy_score(dims)} defects={(round_defects[:2] if score_ok else ['(score_fail)'])}"
            )

            best_total = float(best_round["total"]) if best_round and best_round.get("total") is not None else None
            from skills_kit.prompt_scale import classify_subject

            subject_kind = classify_subject(
                goal=str(bot.get("goal") or ""),
                module=str(bot.get("module") or ""),
                ref_image=str(bot.get("ref_image") or ""),
            )
            defect_text = "；".join(str(x) for x in (round_defects or []))
            stop = decide_round_stop(
                score_ok=score_ok,
                total=total,
                dims=dims if score_ok else None,
                round_num=r,
                min_rounds=min_r,
                threshold=args.threshold,
                anatomy_floor=args.anatomy_floor,
                best_total=best_total,
                no_improve_streak=no_improve_streak,
                plateau_rounds=args.plateau_rounds,
                regression_drop=args.regression_drop,
                subject_kind=subject_kind,
                defects=defect_text,
                style_text=" ".join(
                    str(bot.get(k) or "") for k in ("goal", "module", "ref_image")
                ),
            )
            if stop:
                stop_reason = stop
                best_round = pick_best_round_on_stop(
                    stop_reason=stop,
                    best_round=best_round,
                    current=rec,
                    anatomy_floor=args.anatomy_floor,
                    subject_kind=subject_kind,
                    style_text=" ".join(
                        str(bot.get(k) or "") for k in ("goal", "module", "ref_image")
                    ),
                )
                break

            # Next pad + defects: score failure must not advance the chain
            if score_ok:
                defects = list(round_defects[:4])
                force_ref = should_force_ref_pad(
                    pad_mode=args.pad,
                    total=total,
                    threshold=args.threshold,
                    dims=dims,
                    anatomy_floor=args.anatomy_floor,
                )
                src = (
                    ref
                    if force_ref
                    else choose_next_pad(
                        mode=args.pad,
                        ref=ref,
                        current_out=r_path,
                        score_ok=True,
                        total=total,
                        best_total=best_total,
                        auto_drop=args.auto_pad_drop,
                    )
                )
            else:
                # keep defects/dims; do not update src — always fall back to style_ref
                src = ref

        # promote best to final filename
        if best_round is None:
            return {"bot_id": bid, "ok": False, "error": "no scored rounds", "rounds": rounds}

        best_src = out_dir / best_round["filename"]
        shutil.copy2(best_src, final_path)

        # also store final score under bot:: key
        final_score = float(best_round.get("total") or 0)
        bot_score_key = f"bot::{final_path.name}"
        # reuse scored record of best round if present
        best_sk = f"round::{stem}::r{best_round['round']}"
        if best_sk in scores.get("images", {}):
            fr = dict(scores["images"][best_sk])
            fr["id"] = bot_score_key
            fr["filename"] = final_path.name
            fr["path"] = str(final_path)
            fr["role"] = "bot"
            fr["round"] = best_round["round"]
            scores["images"][bot_score_key] = fr
            atomic_write_json(scores_path, scores)

        result = {
            "bot_id": bid,
            "ok": True,
            "final": str(final_path),
            "final_filename": final_path.name,
            "final_score": final_score,
            "final_dims": best_round.get("dims") or {},
            "final_defects": best_round.get("defects") or [],
            "best_round": best_round["round"],
            "n_rounds": len(rounds),
            "min_rounds_before_stop": min_r,
            "stop_reason": stop_reason,
            "reached_threshold": bool(
                final_score >= args.threshold
                and (anatomy_score(best_round.get("dims") or {}) is not None)
                and float(anatomy_score(best_round.get("dims") or {}) or 0) >= args.anatomy_floor
            ),
            "pad_mode": args.pad,
            "anatomy_floor": args.anatomy_floor,
            "anatomy_blocked_rounds": anatomy_blocked,
            "display_scale": bot["display_scale"],
            "api_scale": bot["api_scale"],
            "slug": bot["slug"],
            "prompt_mode": bot.get("prompt_mode"),
            "aspect_ratio": bot.get("aspect_ratio"),
            "rounds": rounds,
        }
        log(
            f"DONE {bid} stop={stop_reason} best_r={best_round['round']} "
            f"score={final_score} n={len(rounds)} >=9.60={result['reached_threshold']}"
        )
        return result

    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as ex:
        futs = {ex.submit(run_bot, b): b for b in bots}
        for fut in as_completed(futs):
            b = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:
                rec = {"bot_id": b["bot_id"], "ok": False, "error": f"{type(e).__name__}: {e}"}
            results.append(rec)
            manifest["items"][b["bot_id"]] = rec
            atomic_write_json(manifest_path, manifest)

    ok = [r for r in results if r.get("ok")]
    fail = [r for r in results if not r.get("ok")]
    reached = [r for r in ok if r.get("reached_threshold")]
    summary = {
        "version": "v8_20_skill",
        "threshold": args.threshold,
        "max_rounds": args.max_rounds,
        "n_ok": len(ok),
        "n_fail": len(fail),
        "n_reached_9_60": len(reached),
        "mean_final": round(sum(float(r.get("final_score") or 0) for r in ok) / len(ok), 3) if ok else None,
        "round_dist": {},
        "stop_reasons": {},
        "not_reached": [
            {"bot_id": r["bot_id"], "score": r.get("final_score"), "stop": r.get("stop_reason"), "n_rounds": r.get("n_rounds")}
            for r in ok if not r.get("reached_threshold")
        ],
        "failures": fail,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    from collections import Counter
    summary["round_dist"] = dict(Counter(int(r.get("n_rounds") or 0) for r in ok))
    summary["stop_reasons"] = dict(Counter(str(r.get("stop_reason")) for r in ok))
    atomic_write_json(out_dir / "SCORE_SUMMARY.json", summary)

    md = [
        f"# V8-20 skill converge summary",
        f"- threshold: **≥ {args.threshold}** · max_rounds: **{args.max_rounds}**",
        f"- ok: {len(ok)}/{len(results)} · reached≥9.60: **{len(reached)}** · mean: {summary['mean_final']}",
        f"- round_dist: {summary['round_dist']}",
        f"- stop_reasons: {summary['stop_reasons']}",
        "",
        "## Not reached",
    ]
    for row in summary["not_reached"]:
        md.append(f"- {row['bot_id']}: score={row['score']} stop={row['stop']} rounds={row['n_rounds']}")
    if fail:
        md.append("\n## Failures")
        for f in fail:
            md.append(f"- {f.get('bot_id')}: {f.get('error')}")
    (out_dir / "SCORE_SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    log(f"ALL DONE ok={len(ok)} fail={len(fail)} reached={len(reached)} mean={summary['mean_final']}")
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
