#!/usr/bin/env python3
"""V8-20 skill-contract converge v2fix: pad=auto default, anatomy <7.5 veto, safe R4+ drop stop.

Changes vs run_v8_20_skill_converge.py:
1. Pad default `auto`: R1 edits from style_ref; chain previous round only when score improves and
   anatomy is not vetoed (>=7.5), else reset to style_ref. (--pad {ref,previous,auto}).
2. STOP if total≥9.60 AND perspective_anatomy≥7.5 (one-vote veto only on severe meltdown <7.5) AND r≥min_rounds;
   safe early-stop only when r>=4 and 2 consecutive rounds drop >0.5 below best — promote best.
   Tracks both `n_reached_9_60` (anat>=7.5) and `n_reached_9_60_and_anat_8_5` (anat>=8.5).
3. Score fail: retry once; if still fail, do NOT update src/defects with boilerplate.
4. Defect rewrite: map low dims → anatomy/texture/light specific fixes; 【回流修正】≤2;
   subject/module-aware R1 structure floor via build_r1_structure_floor().

Output: generated_v8_20_skill_v2fix/
Never prints API keys.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
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
    build_r1_structure_floor,
    compose_style_first_prompt,
    find_affirmative_lock_hits,
    get_converge_scale_profile,
    strip_affirmative_locks_from_prompt,
)
from skills_kit.prompt_scale import DEFAULT_MAX_ROUNDS, DEFAULT_THRESHOLD  # noqa: E402
from skills_kit.converge_judge_bridge import score_for_converge  # noqa: E402
from skills_kit.skill_image_gen import fan_or_generate_image_job, try_apikey_fan  # noqa: E402
from absolute_5d_scorer import rewrite_prompt_from_defects  # noqa: E402

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


CASE_ANAT_FIX = {
    "night_city": "孤侠落脚与屋脊接触阴影清楚，持剑手腕与剑柄连接可读",
    "pastel_sketch": "屈膝少女手指/腕关节与衣褶遮挡关系清楚，勿融化",
    "sunlit_portrait": "肩颈锁骨与发际衔接稳定，二分光下面部平面分面清楚",
    "ishtar_canyon": "龙翼根/腹与桥体承托清楚，旅人尺度与阶梯透视一致",
}

DIM_FIX = {
    "composition": "强化主体锚点与缩略可读层级，减少纹理/道具争抢注意力",
    "lighting_color": "明确主光方向与接触阴影，避免过曝糊边与无源高光",
    "perspective_anatomy": "修正关节/肢体/持物连接与透视收束，补全接触阴影与结构承托",
    "texture_detail": "稳住边缘与材质区分，避免涂抹融化与重复瓦片/噪点冒充细节",
    "spec_style": "锁回目标画风笔触与色板，禁止混装异风材质",
}

_log_lock = threading.Lock()

_quota_abort = threading.Event()


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


def defects_from_dims(dims: dict, existing: list[str] | None = None, slug: str = "") -> list[str]:
    """Map low dims → specific fix lines; prefer anatomy when lowest; ≤2 items."""
    scored: list[tuple[str, float]] = []
    for k, v in (dims or {}).items():
        try:
            fv = float(v)
        except Exception:
            continue
        if fv < 8.5:
            scored.append((k, fv))
    scored.sort(key=lambda x: x[1])  # lowest first
    # prefer anatomy if it is among the two lowest or is the absolute lowest
    ordered: list[str] = []
    if scored and scored[0][0] == "perspective_anatomy":
        ordered.append(DIM_FIX["perspective_anatomy"])
        for k, _ in scored[1:]:
            if k in DIM_FIX and DIM_FIX[k] not in ordered:
                ordered.append(DIM_FIX[k])
            if len(ordered) >= 2:
                break
    else:
        # if anatomy is low, put it first anyway when it's the lowest among lows
        anat = next(((k, v) for k, v in scored if k == "perspective_anatomy"), None)
        others = [(k, v) for k, v in scored if k != "perspective_anatomy"]
        if anat and (not others or anat[1] <= others[0][1] + 0.5):
            ordered.append(DIM_FIX["perspective_anatomy"])
        for k, _ in (others if not ordered else others):
            if k in DIM_FIX and DIM_FIX[k] not in ordered:
                ordered.append(DIM_FIX[k])
            if len(ordered) >= 2:
                break
        if not ordered and scored:
            k = scored[0][0]
            ordered.append(DIM_FIX.get(k, f"{k}偏低需修正"))

    # keep up to 1 concrete VLM defect if useful and not boilerplate
    for d in existing or []:
        ds = (d or "").strip()
        if not ds:
            continue
        if "体积光" in ds and "边缘完整" in ds:
            continue  # skip blank fallback boilerplate
        if "强化档位意图" in ds:
            continue
        if ds not in ordered:
            # prefer replacing second slot with concrete defect when we already have anatomy
            if len(ordered) < 2:
                ordered.append(ds[:80])
            elif "perspective_anatomy" in str(ordered[0]) or "关节" in ordered[0] or "透视" in ordered[0]:
                # keep anatomy, swap second for concrete if second is generic dim-fix
                ordered[1] = ds[:80]
            break
        if len(ordered) >= 2:
            break
    # case-specific anatomy patch only when perspective_anatomy is actually low (<8.5)
    has_anat_low = any(k == "perspective_anatomy" for k, _ in scored)
    if slug and (has_anat_low or any("关节" in x or "透视" in x for x in ordered)):
        case_fix = CASE_ANAT_FIX.get(slug)
        if case_fix:
            if len(ordered) < 2:
                ordered.append(case_fix)
            else:
                # replace second slot with case-specific if first is anatomy generic
                ordered[1] = case_fix
    return ordered[:2]


def compose_prompt(
    bot: dict,
    best_doc: dict,
    round_num: int = 1,
    defects: list[str] | None = None,
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
        import re as _re
        composed = _re.sub(r"(?:约束：)?保持原图画风笔触与色板；?", "", composed)
        composed = _re.sub(r"保画风色板，按「[^」]*」重构机位\s*\|\s*", "", composed)
        composed = _re.sub(r"\s*\|\s*\|\s*", " | ", composed).strip(" |")
    else:
        prof = get_converge_scale_profile(
            api,
            recompose_dir=recompose_dir,
            goal=bot.get("goal") or "",
            ref_image=bot.get("ref_image") or "",
            module=bot.get("module") or "",
        )
        composed = compose_style_first_prompt(base, prof)
        # Safe subject/module-aware R1 floor: character gets joint/eye/grip floor; pure scene gets perspective/shadow floor
        if round_num == 1:
            floor = build_r1_structure_floor(
                goal=bot.get("goal") or "",
                ref_image=bot.get("ref_image") or "",
                module=bot.get("module") or "",
            )
            if floor and floor not in composed:
                composed = composed.rstrip(" |") + " | " + floor

    if round_num >= 2 and defects:
        # custom short reflow: ≤2 items, no blank 体积光 fallback
        fix = [d.strip() for d in defects if (d or "").strip()][:2]
        # keep V2 goal/recompose intent via rewrite helper but cap fixes
        composed = rewrite_prompt_from_defects(
            composed,
            defects=fix,
            intent=None,
            api_scale=api,
            recompose_dir="" if mode == "style_jump" else recompose_dir,
        )
        # rewrite_prompt_from_defects may append high-scale 体积光 — trim 【回流修正】 to ≤2
        if "【回流修正】" in composed:
            head, _, tail = composed.partition("【回流修正】")
            # strip the helper's auto high-volume-light if we already have 2 anatomy/texture fixes
            parts = [p.strip() for p in tail.split("；") if p.strip()]
            # drop generic volume-light when we have specific defects
            cleaned = []
            for p in parts:
                if "加强体积光" in p and cleaned:
                    continue
                cleaned.append(p)
            composed = head.rstrip(" |") + " | 【回流修正】" + "；".join(cleaned[:2])
    return composed


def edit_image(
    *,
    env: dict[str, str],
    model: str,
    src: Path | None,
    prompt: str,
    size: str,
    out_path: Path,
    timeout: int = 240,
    aspect_ratio: str = "1:1",
    bot_id: str = "",
    round_num: int = 0,
) -> dict[str, Any]:
    del env, model, timeout  # apikey-image script owns auth/model
    t0 = time.time()
    fan = try_apikey_fan(prompt=prompt, out_path=out_path, pad_src=src, aspect_ratio=aspect_ratio)
    if fan.get("ok"):
        fan["elapsed"] = round(time.time() - t0, 1)
        return fan
    job = fan_or_generate_image_job(
        prompt=prompt,
        out_path=out_path,
        pad_src=src,
        aspect_ratio=aspect_ratio,
        bot_id=bot_id,
        round_num=round_num,
    )
    job["elapsed"] = round(time.time() - t0, 1)
    if job.get("balance_exhausted"):
        log(f"  apikey.fan balance low on {out_path.name} → defer to cursor.GenerateImage")
    return job


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
    scale_prof = get_converge_scale_profile(
        str((bot or {}).get("api_scale") or "medium"),
        goal=goal or (bot or {}).get("goal") or "",
        ref_image=(bot or {}).get("ref_image") or "",
    )
    item["ref_image"] = (bot or {}).get("ref_image") or ""
    return score_for_converge(
        item,
        env,
        model,
        root=REPO,
        scale_prof=scale_prof,
        goal=goal or (bot or {}).get("goal") or "",
    )


def score_with_retry(
    *,
    path: Path,
    env: dict[str, str],
    model: str,
    role: str,
    bot: dict | None = None,
    round_num: int | None = None,
    goal: str = "",
) -> dict[str, Any]:
    scored = score_image(path=path, env=env, model=model, role=role, bot=bot, round_num=round_num, goal=goal)
    if scored.get("ok"):
        return scored
    log(f"  score fail once, retrying… err={(scored.get('error') or scored.get('raw') or '')!s}"[:180])
    time.sleep(2)
    scored2 = score_image(path=path, env=env, model=model, role=role, bot=bot, round_num=round_num, goal=goal)
    if scored2.get("ok"):
        scored2["score_retried"] = True
        return scored2
    scored2["score_retried"] = True
    scored2["score_fail_double"] = True
    return scored2


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


def anat_of(rec: dict | None) -> float | None:
    if not rec:
        return None
    dims = rec.get("dims") or {}
    try:
        return float(dims.get("perspective_anatomy"))
    except Exception:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--env", default="/home/box/.config/pmem-art/apikey_fan.env")
    ap.add_argument("--gen-model", default="gpt-image-2")
    ap.add_argument("--score-model", default="gpt-6-sol")
    ap.add_argument("--out-dir", default=str(REPO / "generated_v8_20_skill_v2fix"))
    ap.add_argument("--concurrency", type=int, default=2)
    ap.add_argument("--threshold", type=float, default=float(DEFAULT_THRESHOLD))
    ap.add_argument("--anat-gate", type=float, default=7.5, help="one-vote veto floor: forbid STOP when perspective_anatomy < this (default 7.5)")
    ap.add_argument("--max-rounds", type=int, default=int(DEFAULT_MAX_ROUNDS))
    ap.add_argument("--pad", choices=("ref", "previous", "auto"), default="auto",
                    help="edit pad source: ref=always style_ref; previous=chain; auto=chain if improved else reset")
    ap.add_argument("--early-stop-min-round", type=int, default=4, help="only enable early-stop after this round (default 4)")
    ap.add_argument("--drop-stop", type=float, default=0.5, help="early-stop if 2 consecutive rounds drop > this below best after R4")
    ap.add_argument("--drop-streak", type=int, default=2, help="consecutive rounds below (best - drop_stop) required to stop")
    ap.add_argument("--plateau-rounds", type=int, default=0, help="optional stop if N rounds with no new best (0=off)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--skip-baselines", action="store_true")
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
        "version": "v8_20_skill_v2fix",
        "threshold": args.threshold,
        "anat_gate": args.anat_gate,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "plateau_rounds": args.plateau_rounds,
        "drop_stop": args.drop_stop,
        "source": "skills_kit DEFAULT_THRESHOLD / DEFAULT_MAX_ROUNDS + v2fix pad/stop/defect",
        "gen_model": args.gen_model,
        "score_model": args.score_model,
        "bot_ids": [b["bot_id"] for b in bots],
        "count": len(bots),
    }
    atomic_write_json(out_dir / "contract.json", contract)
    log(
        f"skill-converge-v2fix bots={len(bots)} threshold={args.threshold} anat≥{args.anat_gate} "
        f"max_rounds={args.max_rounds} pad={args.pad} out={out_dir} gen={args.gen_model} score={args.score_model}"
    )

    for name, rel, _slug, _ar in REF_FILES:
        src = REPO / rel
        dst = out_dir / name
        if src.is_file() and (args.force or not dst.is_file()):
            shutil.copy2(src, dst)

    scores_path = out_dir / "vlm_scores.json"
    scores = json.loads(scores_path.read_text()) if scores_path.is_file() else {
        "version": "v8_20_skill_v2fix",
        "model": args.score_model,
        "threshold": args.threshold,
        "images": {},
        "failures": {},
    }

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
            rec = score_with_retry(path=p, env=env, model=args.score_model, role="baseline", goal=f"baseline {slug}")
            if rec.get("ok"):
                scores["images"][key] = rec
            else:
                scores["failures"][key] = rec
            atomic_write_json(scores_path, scores)
            log(f"  baseline {name} total={rec.get('total')} ok={rec.get('ok')}")

    for b in bots:
        p1 = compose_prompt(b, best, 1)
        hits = find_affirmative_lock_hits(p1)
        if hits:
            log(f"ABORT lock hits {b['bot_id']}: {hits}")
            return 2

    manifest_path = out_dir / "gen_manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.is_file() else {
        "version": "v8_20_skill_v2fix",
        "threshold": args.threshold,
        "anat_gate": args.anat_gate,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "items": {},
    }
    # thread-safe manifest/scores writes
    io_lock = threading.Lock()

    def run_bot(bot: dict) -> dict[str, Any]:
        bid = bot["bot_id"]
        stem = f"{bid}_{bot['slug']}_{bot['display_scale']}"
        final_path = out_dir / f"{stem}.jpg"
        min_r = min_rounds_for(bot)
        size = AR_SIZE.get(bot.get("aspect_ratio") or "1:1", "1024x1024")
        ref = REPO / bot["ref_image"]
        if not ref.is_file():
            return {"bot_id": bid, "ok": False, "error": f"missing ref {ref}"}

        prev = manifest.get("items", {}).get(bid) or {}
        if (
            not args.force
            and final_path.is_file()
            and prev.get("ok")
            and prev.get("stop_reason") in (
                "STOP_TARGET_REACHED",
                "max_rounds_reached",
                "STOP_PLATEAU",
                "STOP_DROP",
            )
        ):
            log(f"skip done {bid} stop={prev.get('stop_reason')} score={prev.get('final_score')}")
            return prev

        rounds: list[dict[str, Any]] = []
        defects: list[str] = []
        best_round = None
        stop_reason = "max_rounds_reached"
        no_improve = 0
        drop_streak = 0
        last_ok_total: float | None = None
        is_bold = (bot.get("prompt_mode") == "style_jump") or (bot.get("display_scale") == "recompose_bold")
        pad_src: Path | None = None if is_bold else ref

        for r in range(1, args.max_rounds + 1):
            if _quota_abort.is_set():
                if best_round is not None:
                    stop_reason = "STOP_QUOTA"
                    break
                return {"bot_id": bid, "ok": False, "error": "insufficient_quota", "rounds": rounds, "phase": f"r{r}"}
            prompt = compose_prompt(bot, best, r, defects=defects if r >= 2 else None)
            r_path = out_dir / f"{stem}_r{r}.jpg"

            # low/medium/high/recompose: every round pads the original ref.
            # style_jump pads nothing. pad=previous is the explicit chain override.
            if is_bold:
                pad_src = None
            elif args.pad != "previous":
                pad_src = ref

            ar = bot.get("aspect_ratio") or "1:1"
            pad_name = pad_src.name if pad_src is not None else "(no pad)"
            log(f"GEN {bid} R{r}/{args.max_rounds} min_stop={min_r} pad={args.pad}:{pad_name} -> {r_path.name}")
            gen = edit_image(
                env=env,
                model=args.gen_model,
                src=pad_src,
                prompt=prompt,
                size=size,
                out_path=r_path,
                aspect_ratio=ar,
                bot_id=bid,
                round_num=r,
            )
            if gen.get("needs_agent_gen"):
                return {
                    "bot_id": bid,
                    "ok": False,
                    "phase": f"r{r}_gen_pending",
                    "pending_gen": gen.get("agent_job"),
                    "fan_error": gen.get("fan_error"),
                    "rounds": rounds,
                }
            if not gen.get("ok"):
                return {
                    "bot_id": bid,
                    "ok": False,
                    "phase": f"r{r}",
                    "error": gen.get("error") or gen.get("fan_error"),
                    "rounds": rounds,
                }

            log(f"SCORE {bid} R{r}")
            scored = score_with_retry(
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
            raw_defects = scored.get("defects") or [] if score_ok else []
            if isinstance(raw_defects, str):
                raw_defects = [raw_defects]

            if score_ok:
                round_defects = defects_from_dims(dims, raw_defects, slug=bot.get("slug") or "")
            else:
                round_defects = list(defects) if defects else []
                if scored.get("judge_pending") == "agent":
                    log(f"  {bid} R{r} VLM unavailable — need Agent judge")
                    return {
                        "bot_id": bid,
                        "ok": False,
                        "phase": f"r{r}_judge_pending",
                        "pending_judge": {
                            "image": str(r_path),
                            "error": scored.get("error"),
                        },
                        "rounds": rounds,
                    }
                log(f"  {bid} R{r} SCORE FAIL (double) — keep prior defects, skip pad chain")

            rec = {
                "round": r,
                "filename": r_path.name,
                "prompt": prompt,
                "pad_src": pad_src.name if pad_src is not None else None,
                "pad_mode": args.pad,
                "elapsed": gen.get("elapsed"),
                "bytes": gen.get("bytes"),
                "score_ok": score_ok,
                "total": total,
                "dims": dims,
                "defects": round_defects[:4],
                "grade": scored.get("grade") if score_ok else None,
                "score_fail_double": bool(scored.get("score_fail_double")),
            }
            rounds.append(rec)
            sk = f"round::{stem}::r{r}"
            with io_lock:
                if score_ok:
                    scores["images"][sk] = scored
                    scores.get("failures", {}).pop(sk, None)
                else:
                    scores.setdefault("failures", {})[sk] = scored
                atomic_write_json(scores_path, scores)

            anat = anat_of(rec) if score_ok else None
            # Fail-closed: missing anatomy cannot unlock STOP / chain pad.
            anat_ok = bool(score_ok and anat is not None and anat >= args.anat_gate)
            rec["anat_ok"] = anat_ok

            improved = False
            if total is not None:
                if best_round is None:
                    best_round = rec
                    no_improve = 0
                    improved = True
                else:
                    best_anat_ok = bool(best_round.get("anat_ok", True))
                    best_total = float(best_round.get("total") or -1)
                    # Non-vetoed round (anat >= anat_gate) always beats a vetoed round (< anat_gate)
                    if (anat_ok and not best_anat_ok) or (anat_ok == best_anat_ok and total > best_total):
                        best_round = rec
                        no_improve = 0
                        improved = True
                    elif score_ok:
                        no_improve += 1

            log(f"  {bid} R{r} total={total} anat={anat} anat_ok={anat_ok} defects={round_defects[:2]} no_improve={no_improve}")

            # STOP: threshold + anatomy one-vote veto (anat >= anat_gate) + min rounds
            if (
                total is not None
                and total >= args.threshold
                and anat_ok
                and r >= min_r
            ):
                stop_reason = "STOP_TARGET_REACHED"
                best_round = rec
                break

            # Safe early-stop: only active when r >= early_stop_min_round (default 4)
            # Requires `drop_streak` (default 2) consecutive rounds below (best_total - drop_stop) where drop_stop=0.5
            if (
                args.drop_stop > 0
                and total is not None
                and best_round is not None
                and best_round["round"] != r
                and float(best_round.get("total") or 0) - total > args.drop_stop
            ):
                drop_streak += 1
            elif score_ok:
                drop_streak = 0

            if (
                args.drop_stop > 0
                and r >= args.early_stop_min_round
                and r >= min_r
                and drop_streak >= args.drop_streak
                and best_round is not None
            ):
                stop_reason = "STOP_DROP"
                log(
                    f"  {bid} SAFE DROP stop at R{r}: {drop_streak} consecutive rounds below "
                    f"best={best_round.get('total')} by >{args.drop_stop} (cur={total})"
                )
                break

            # STOP: plateau (N rounds no new best), only when args.plateau_rounds > 0 and r >= early_stop_min_round
            if (
                args.plateau_rounds > 0
                and r >= args.early_stop_min_round
                and no_improve >= args.plateau_rounds
                and r >= min_r
                and best_round is not None
            ):
                stop_reason = "STOP_PLATEAU"
                log(f"  {bid} PLATEAU stop at R{r} after {no_improve} non-improving rounds")
                break

            # prepare next round pad + defects
            if not score_ok:
                # keep previous defects; do not chain an unscored plate
                if is_bold:
                    pad_src = None
                elif args.pad == "previous" and best_round is not None:
                    pad_src = out_dir / best_round["filename"]
                else:
                    pad_src = ref
                continue

            defects = list(round_defects[:2])
            if is_bold:
                pad_src = None
            elif args.pad == "previous":
                pad_src = r_path
            else:
                pad_src = ref
            last_ok_total = total if (total is not None and anat_ok) else last_ok_total

        if best_round is None:
            # maybe only score-failed rounds — still try last image if any
            if rounds:
                best_round = rounds[-1]
            else:
                return {"bot_id": bid, "ok": False, "error": "no rounds", "rounds": rounds}

        best_src = out_dir / best_round["filename"]
        if best_src.is_file():
            shutil.copy2(best_src, final_path)
        else:
            return {"bot_id": bid, "ok": False, "error": f"missing best {best_src}", "rounds": rounds}

        final_score = float(best_round.get("total") or 0) if best_round.get("score_ok") else None
        bot_score_key = f"bot::{final_path.name}"
        best_sk = f"round::{stem}::r{best_round['round']}"
        with io_lock:
            if best_sk in scores.get("images", {}):
                fr = dict(scores["images"][best_sk])
                fr["id"] = bot_score_key
                fr["filename"] = final_path.name
                fr["path"] = str(final_path)
                fr["role"] = "bot"
                fr["round"] = best_round["round"]
                scores["images"][bot_score_key] = fr
                atomic_write_json(scores_path, scores)

        anat_val = anat_of(best_round)
        reached = (
            final_score is not None
            and final_score >= args.threshold
            and anat_val is not None
            and anat_val >= args.anat_gate
        )
        reached_anat_85 = (
            final_score is not None
            and final_score >= args.threshold
            and (anat_val is not None and anat_val >= 8.5)
        )
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
            "reached_threshold": bool(reached),
            "reached_anat_8_5": bool(reached_anat_85),
            "pad_mode": args.pad,
            "display_scale": bot["display_scale"],
            "api_scale": bot["api_scale"],
            "slug": bot["slug"],
            "prompt_mode": bot.get("prompt_mode"),
            "aspect_ratio": bot.get("aspect_ratio"),
            "rounds": rounds,
        }
        log(
            f"DONE {bid} stop={stop_reason} best_r={best_round['round']} "
            f"score={final_score} anat={anat_of(best_round)} n={len(rounds)} "
            f">=9.60+anat={result['reached_threshold']}"
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
            with io_lock:
                manifest["items"][b["bot_id"]] = rec
                atomic_write_json(manifest_path, manifest)

    ok = [r for r in results if r.get("ok")]
    fail = [r for r in results if not r.get("ok")]
    reached = [r for r in ok if r.get("reached_threshold")]
    scored_ok = [r for r in ok if isinstance(r.get("final_score"), (int, float))]
    summary = {
        "version": "v8_20_skill_v2fix",
        "threshold": args.threshold,
        "anat_gate": args.anat_gate,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "n_ok": len(ok),
        "n_fail": len(fail),
        "n_reached_9_60": len(reached),
        "n_reached_9_60_and_anat_8_5": sum(1 for r in ok if r.get("reached_anat_8_5")),
        "mean_final": round(sum(float(r["final_score"]) for r in scored_ok) / len(scored_ok), 3) if scored_ok else None,
        "min_final": round(min(float(r["final_score"]) for r in scored_ok), 3) if scored_ok else None,
        "max_final": round(max(float(r["final_score"]) for r in scored_ok), 3) if scored_ok else None,
        "round_dist": {},
        "stop_reasons": {},
        "not_reached": [
            {
                "bot_id": r["bot_id"],
                "score": r.get("final_score"),
                "anat": (r.get("final_dims") or {}).get("perspective_anatomy"),
                "stop": r.get("stop_reason"),
                "n_rounds": r.get("n_rounds"),
            }
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
        f"# V8-20 skill converge v2fix summary",
        f"- threshold: **≥ {args.threshold}** · anat_gate: **≥ {args.anat_gate}** · max_rounds: **{args.max_rounds}** · pad: **{args.pad}**",
        f"- ok: {len(ok)}/{len(results)} · reached≥9.60(anat≥{args.anat_gate}): **{len(reached)}** · reached≥9.60+anat≥8.5: **{summary['n_reached_9_60_and_anat_8_5']}** · mean: {summary['mean_final']} · range: {summary['min_final']}–{summary['max_final']}",
        f"- round_dist: {summary['round_dist']}",
        f"- stop_reasons: {summary['stop_reasons']}",
        "",
        "## Not reached",
    ]
    for row in summary["not_reached"]:
        md.append(
            f"- {row['bot_id']}: score={row['score']} anat={row['anat']} stop={row['stop']} rounds={row['n_rounds']}"
        )
    if fail:
        md.append("\n## Failures")
        for f in fail:
            md.append(f"- {f.get('bot_id')}: {f.get('error')}")
    (out_dir / "SCORE_SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    log(f"ALL DONE ok={len(ok)} fail={len(fail)} reached={len(reached)} mean={summary['mean_final']}")
    return 0 if not fail else 1


if __name__ == "__main__":
    raise SystemExit(main())
