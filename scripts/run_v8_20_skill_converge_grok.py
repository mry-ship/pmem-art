#!/usr/bin/env python3
"""V8-20 skill converge with Grok Bot GenerateImage (tool-driven waves).

Same policy as run_v8_20_skill_converge_v2fix.py:
  threshold 9.6, anat gate 7.5, max 8 rounds, pad=auto, drop-stop after R4.

Generation is NOT done here — agent fulfills jobs via Cursor GenerateImage.
Commands:
  init
  next-jobs [--limit N]
  ingest --bot-id ID --round N --image PATH
  finalize
  status
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from run_v8_20_skill_converge_v2fix import (  # noqa: E402
    REF_FILES,
    WANT_SCALES,
    anat_of,
    compose_prompt,
    defects_from_dims,
    load_env,
    min_rounds_for,
    score_with_retry,
    select_bots,
    sha256_file,
)
from skills_kit import find_affirmative_lock_hits  # noqa: E402
from absolute_5d_scorer import absolute_5d  # noqa: E402

DEFAULT_OUT = REPO / "generated_v8_20_skill_grok_v4"
STATE_NAME = "orchestrator_state.json"

AR_OK = {"1:1", "4:3", "3:4", "16:9", "9:16"}

# --- v2 levers (user-approved) ---
FORCE_REF_PAD_IF_R1_GE = 8.2
# Round2: NEVER chain a weak gen as pad — if this round < bar, next pad = style_ref
FORCE_REF_IF_TOTAL_LT = 8.2
EARLY_STOP_R1_GE = 8.2  # Round3: align with force_ref bar; save gens on strong r1
ANATOMY_LOCK = (
    "解剖锁：correct human anatomy, five fingers on each hand, coherent joints, "
    "no warped limbs; portraits: clear iris/pupils, both eyes aligned"
)
MICRO_DETAIL_LOCK = (
    "微细节：fine grain fabric weave, pore-level skin texture where visible, "
    "crisp specular edges; avoid over-smooth plastic melt"
)
TEXTURE_MATERIAL_LOCK = (
    "材质锁：distinct material edges stone vs cloth vs scale vs skin; "
    "NO repeated tile noise, NO melted paint smears pretending detail"
)
SCENE_LOCK_ISHTAR = (
    "场景锁：eye-level stone terrace + three-arch canyon bridge + flying dragon; "
    "FORBID top-down alley / courtyard shaft / worm's-eye plunge"
)
CONTACT_LOCK_NIGHT = (
    "接触锁：swordsman foot-to-roof-ridge contact shadow readable; "
    "sword wrist-to-hilt join continuous; NO floating feet"
)
SOFT_RECOMPOSE = (
    "机位软改：mild crop / same lens family toward the stated camera; "
    "NO extreme FOV, NO fisheye, NO bold redesign of identity or style bible"
)
SOFT_BOLD = (
    "风格软跳：keep silhouette + AR; mild style accent only; "
    "NO extreme FOV / bold redesign; preserve readable anatomy and lighting continuity"
)
# Round3 priority = Round2 worst (texture kept; fix bold-pad fight + night lighting)
PRIORITY_BOT_ORDER = [
    "v8_bot_06", "v8_bot_02", "v8_bot_16", "v8_bot_26",
    "v8_bot_04", "v8_bot_10", "v8_bot_30", "v8_bot_28",
]
LIGHTING_NIGHT_LOCK = (
    "夜城光锁：warm golden lantern volume light + teal/orange collision + readable rim; "
    "FORBID flat charcoal underexposure / muddy grey wash"
)
SPEC_MEDIUM_LOCK = (
    "媒介锁：preserve the named medium (ink-wash / pastel grain / film thick-paint / concept oil); "
    "NO accidental style bible swap"
)


def compose_prompt_v2(bot: dict, best_doc: dict, round_num: int = 1, defects: list[str] | None = None) -> str:
    """compose_prompt + Round3 soften/bold-pad fix + anatomy/micro/texture/lighting locks."""
    p = compose_prompt(bot, best_doc, round_num, defects=defects)
    api = (bot.get("api_scale") or "").lower()
    mode = bot.get("prompt_mode") or ""
    display = bot.get("display_scale") or ""
    slug = bot.get("slug") or ""
    is_bold = display == "recompose_bold" or mode == "style_jump"
    is_recompose = (api == "recompose" or display == "recompose") and not is_bold

    # Soften aggressive recompose / bold language (Round3: strip 跳变 hard)
    if is_bold:
        for bad in (
            "风格圣经按目标大跳", "风格叙事大跳", "风格圣经跳变", "风格跳变", "跳变",
            "大改 style_jump", "extreme", "fisheye", "极端广角",
        ):
            p = p.replace(bad, "温和媒介强调")
        if SOFT_BOLD not in p:
            p = p.rstrip(" |") + " | " + SOFT_BOLD
    elif is_recompose:
        p = p.replace("按「", "mild crop toward「")
        if SOFT_RECOMPOSE not in p:
            p = p.rstrip(" |") + " | " + SOFT_RECOMPOSE

    # Soft defect reflow — ONLY for non-recompose/non-bold (avoid fighting camera change)
    if round_num >= 2 and defects and not is_bold and not is_recompose:
        p = p.rstrip(" |") + " | Keep identical composition, camera, pose, crop; fix ONLY named defects."
    elif round_num >= 2 and defects and (is_bold or is_recompose):
        p = p.rstrip(" |") + " | Fix ONLY named anatomy/contact defects; keep the stated camera/style intent."

    # Anatomy + micro-detail on every prompt
    if ANATOMY_LOCK not in p:
        p = p.rstrip(" |") + " | " + ANATOMY_LOCK
    if slug == "sunlit_portrait" and "iris" not in p.lower():
        p = p.rstrip(" |") + " | portrait eyes: distinct iris rings, catchlights, no fused eyelids"
    if MICRO_DETAIL_LOCK not in p:
        p = p.rstrip(" |") + " | " + MICRO_DETAIL_LOCK
    if TEXTURE_MATERIAL_LOCK not in p:
        p = p.rstrip(" |") + " | " + TEXTURE_MATERIAL_LOCK
    if slug == "ishtar_canyon" and SCENE_LOCK_ISHTAR not in p:
        p = p.rstrip(" |") + " | " + SCENE_LOCK_ISHTAR
    if slug == "night_city" and CONTACT_LOCK_NIGHT not in p:
        p = p.rstrip(" |") + " | " + CONTACT_LOCK_NIGHT
    if slug == "night_city" and LIGHTING_NIGHT_LOCK not in p:
        p = p.rstrip(" |") + " | " + LIGHTING_NIGHT_LOCK
    # Round3: bold must NOT match source style_ref (medium fight); others keep hard match
    if is_bold:
        # strip any match-style_ref clause that compose may have added
        if "match style_ref" in p.lower():
            parts = [x for x in p.split(" | ") if "match style_ref" not in x.lower()]
            p = " | ".join(parts)
        if "execute the target medium boldly from text" not in p:
            p = p.rstrip(" |") + " | execute the target medium boldly from text; DO NOT copy source style_ref medium"
    else:
        if SPEC_MEDIUM_LOCK not in p:
            p = p.rstrip(" |") + " | " + SPEC_MEDIUM_LOCK
        if "match style_ref" not in p.lower():
            p = p.rstrip(" |") + " | match style_ref lighting palette and medium exactly; treat refs as hard constraints"
    return p


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def load_json(path: Path, default: Any) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def map_ar(ar: str) -> str:
    a = (ar or "1:1").strip()
    return a if a in AR_OK else "1:1"


def ensure_jpg(src: Path, dst: Path) -> dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve() and dst.suffix.lower() in (".jpg", ".jpeg"):
        return {"ok": True, "path": str(dst), "bytes": dst.stat().st_size, "converted": False}
    img = Image.open(src)
    if img.mode in ("RGBA", "P", "LA"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            bg.paste(img, mask=img.split()[-1])
        else:
            bg.paste(img)
        img = bg
    elif img.mode != "RGB":
        img = img.convert("RGB")
    img.save(dst, "JPEG", quality=92, optimize=True)
    return {"ok": True, "path": str(dst), "bytes": dst.stat().st_size, "converted": True}


def bot_stem(bot: dict) -> str:
    return f"{bot['bot_id']}_{bot['slug']}_{bot['display_scale']}"



def score_offline(path: Path, bot: dict, round_num: int | None = None) -> dict[str, Any]:
    """Offline Absolute-5D checklist (used when VLM balance is exhausted)."""
    ref = REPO / (bot.get("ref_image") or "")
    api = bot.get("api_scale") or "medium"
    mode = bot.get("prompt_mode") or ""
    r = absolute_5d(
        str(path),
        api_scale=api,
        prompt_mode=mode,
        ref_path=str(ref) if ref.is_file() else None,
    )
    dims = dict(r.get("dims") or {})
    total = float(r.get("score") or 0)
    defects = r.get("defects") or []
    if isinstance(defects, str):
        defects = [defects] if defects.strip() else []
    # Heuristic defect hints from low dims
    low = sorted(((k, float(v)) for k, v in dims.items() if v is not None), key=lambda x: x[1])
    for k, v in low[:2]:
        if v < 8.0:
            defects.append(f"{k}偏低({v:.2f})")
    return {
        "ok": True,
        "total": round(total, 3),
        "dims": {k: round(float(v), 3) for k, v in dims.items()},
        "defects": defects[:6],
        "grade": (r.get("bands") or {}).get("total") if isinstance(r.get("bands"), dict) else None,
        "score_backend": "offline_absolute_5d",
        "coverage": r.get("coverage"),
        "id": f"round::{path.name}" + (f"::r{round_num}" if round_num else ""),
        "filename": path.name,
        "path": str(path),
        "role": "round",
        "bot_id": bot.get("bot_id") or "",
        "slug": bot.get("slug") or "",
        "api_scale": api,
        "display_scale": bot.get("display_scale") or "",
        "round": round_num,
        "track": "A_absolute_5d_offline_checklist",
    }


def init_state(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    doc = json.loads((REPO / "bot_tasks_v8.json").read_text())
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text())
    bots = select_bots(doc)
    if args.only:
        keys = [k.strip() for k in args.only.split(",") if k.strip()]
        bots = [b for b in bots if any(k in b["bot_id"] or k in b["display_scale"] or k in b["slug"] for k in keys)]
    if args.limit_bots:
        bots = bots[: args.limit_bots]

    for name, rel, _slug, _ar in REF_FILES:
        src = REPO / rel
        dst = out_dir / name
        if src.is_file():
            shutil.copy2(src, dst)

    for b in bots:
        p1 = compose_prompt_v2(b, best, 1)
        hits = find_affirmative_lock_hits(p1)
        if hits:
            print(f"ABORT lock hits {b['bot_id']}: {hits}", flush=True)
            return 2

    contract = {
        "version": "v8_20_skill_grok_v2",
        "threshold": args.threshold,
        "anat_gate": args.anat_gate,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "drop_stop": args.drop_stop,
        "early_stop_min_round": args.early_stop_min_round,
        "drop_streak": args.drop_streak,
        "gen_engine": "cursor.GenerateImage",
        "score_model": args.score_model,
        "score_backend": args.score_backend,
        "bot_ids": [b["bot_id"] for b in bots],
        "count": len(bots),
        "concurrency_hint": args.concurrency,
        "scorer": "offline_absolute_5d",
        "scorer_note": "gpt-6-sol VLM not used (quota will not be restored); offline Absolute-5D checklist",
        "levers": ["force_ref_pad_if_r1_ge_8.2", "force_ref_if_total_lt_8.2", "soften_recompose_bold", "anatomy_micro_locks", "early_stop_r1_ge_8.5", "texture_material_lock", "scene_lock_ishtar", "lighting_night_lock", "bold_no_style_ref_pad"],
        "priority_bots": PRIORITY_BOT_ORDER,
    }
    atomic_write_json(out_dir / "contract.json", contract)

    state = {
        "version": "v8_20_skill_grok_v2",
        "out_dir": str(out_dir),
        "threshold": args.threshold,
        "anat_gate": args.anat_gate,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "drop_stop": args.drop_stop,
        "early_stop_min_round": args.early_stop_min_round,
        "drop_streak": args.drop_streak,
        "score_model": args.score_model,
        "score_backend": args.score_backend,
        "env_path": args.env,
        "bots": {},
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    for b in bots:
        ref = REPO / b["ref_image"]
        display = b.get("display_scale") or ""
        mode = b.get("prompt_mode") or ""
        is_bold = display == "recompose_bold" or mode == "style_jump"
        state["bots"][b["bot_id"]] = {
            "bot": b,
            "stem": bot_stem(b),
            "status": "active",  # active | done | failed
            "next_round": 1,
            "pad_src": None if is_bold else str(ref),
            "defects": [],
            "rounds": [],
            "best_round": None,
            "no_improve": 0,
            "drop_streak": 0,
            "last_ok_total": None,
            "stop_reason": None,
            "error": None,
            "min_rounds": min_rounds_for(b),
        }

    scores = {
        "version": "v8_20_skill_grok_v2",
        "model": args.score_model,
        "threshold": args.threshold,
        "images": {},
        "failures": {},
    }
    atomic_write_json(out_dir / "vlm_scores.json", scores)
    atomic_write_json(out_dir / "gen_manifest.json", {
        "version": "v8_20_skill_grok_v2",
        "threshold": args.threshold,
        "anat_gate": args.anat_gate,
        "max_rounds": args.max_rounds,
        "pad": args.pad,
        "gen_engine": "cursor.GenerateImage",
        "items": {},
    })
    atomic_write_json(out_dir / STATE_NAME, state)
    print(json.dumps({"ok": True, "bots": len(bots), "out_dir": str(out_dir)}, ensure_ascii=False))
    return 0


def next_jobs(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    state = load_json(out_dir / STATE_NAME, None)
    if not state:
        print(json.dumps({"ok": False, "error": "no state; run init"}, ensure_ascii=False))
        return 1
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text())
    jobs = []
    def _prio(bid: str) -> tuple:
        try:
            return (0, PRIORITY_BOT_ORDER.index(bid))
        except ValueError:
            return (1, bid)
    for bid, st in sorted(state["bots"].items(), key=lambda kv: _prio(kv[0])):
        if st.get("status") != "active":
            continue
        r = int(st["next_round"])
        if r > int(state["max_rounds"]):
            continue
        bot = st["bot"]
        prompt = compose_prompt_v2(bot, best, r, defects=st.get("defects") if r >= 2 else None)
        pad = Path(st["pad_src"]) if st.get("pad_src") else None
        ar = map_ar(bot.get("aspect_ratio") or "1:1")
        stem = st["stem"]
        out_name = f"{stem}_r{r}.jpg"
        jobs.append({
            "bot_id": bid,
            "round": r,
            "stem": stem,
            "prompt": prompt,
            "pad_src": str(pad) if pad is not None else None,
            "aspect_ratio": ar,
            "out_filename": out_name,
            "out_path": str(out_dir / out_name),
            "gen_filename": f"grok_{stem}_r{r}.png",
        })
        if len(jobs) >= args.limit:
            break
    active = sum(1 for st in state["bots"].values() if st.get("status") == "active")
    done = sum(1 for st in state["bots"].values() if st.get("status") == "done")
    failed = sum(1 for st in state["bots"].values() if st.get("status") == "failed")
    print(json.dumps({
        "ok": True,
        "jobs": jobs,
        "counts": {"active": active, "done": done, "failed": failed, "job_batch": len(jobs)},
    }, ensure_ascii=False))
    return 0


def ingest(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    state_path = out_dir / STATE_NAME
    state = load_json(state_path, None)
    if not state:
        print(json.dumps({"ok": False, "error": "no state"}, ensure_ascii=False))
        return 1
    bid = args.bot_id
    st = state["bots"].get(bid)
    if not st:
        print(json.dumps({"ok": False, "error": f"unknown bot {bid}"}, ensure_ascii=False))
        return 1
    if st.get("status") != "active":
        print(json.dumps({"ok": False, "error": f"bot not active: {st.get('status')}", "status": st.get("status")}, ensure_ascii=False))
        return 1
    r = int(args.round)
    if r != int(st["next_round"]):
        print(json.dumps({"ok": False, "error": f"expected round {st['next_round']}, got {r}"}, ensure_ascii=False))
        return 1

    src = Path(args.image)
    if not src.is_file():
        print(json.dumps({"ok": False, "error": f"missing image {src}"}, ensure_ascii=False))
        return 1

    bot = st["bot"]
    stem = st["stem"]
    r_path = out_dir / f"{stem}_r{r}.jpg"
    conv = ensure_jpg(src, r_path)
    pad_src = Path(st["pad_src"]) if st.get("pad_src") else None

    scores_path = out_dir / "vlm_scores.json"
    scores = load_json(scores_path, {"images": {}, "failures": {}})
    backend = (state.get("score_backend") or "offline").lower()  # default offline (VLM balance exhausted)

    scored: dict[str, Any]
    if backend == "offline":
        scored = score_offline(r_path, bot, r)
    elif backend == "vlm":
        env = load_env(Path(state["env_path"]))
        scored = score_with_retry(
            path=r_path,
            env=env,
            model=state["score_model"],
            role="round" if r < state["max_rounds"] else "bot",
            bot=bot,
            round_num=r,
            goal=bot.get("goal") or "",
        )
    else:  # auto: try VLM once lightly, fall back offline on balance/403
        try:
            env = load_env(Path(state["env_path"]))
            scored = score_with_retry(
                path=r_path,
                env=env,
                model=state["score_model"],
                role="round" if r < state["max_rounds"] else "bot",
                bot=bot,
                round_num=r,
                goal=bot.get("goal") or "",
            )
            err = str(scored.get("error") or scored.get("raw") or "")
            if (not scored.get("ok")) and (
                "INSUFFICIENT_BALANCE" in err
                or "Insufficient account balance" in err
                or "HTTP 403" in err
            ):
                scored = score_offline(r_path, bot, r)
                scored["vlm_fallback"] = "offline_absolute_5d"
        except Exception as e:
            scored = score_offline(r_path, bot, r)
            scored["vlm_fallback"] = f"offline_after_exc:{type(e).__name__}"
    score_ok = bool(scored.get("ok"))
    total = float(scored.get("total") or 0) if score_ok else None
    dims = scored.get("dims") or {} if score_ok else {}
    raw_defects = scored.get("defects") or [] if score_ok else []
    if isinstance(raw_defects, str):
        raw_defects = [raw_defects]

    if score_ok:
        round_defects = defects_from_dims(dims, raw_defects, slug=bot.get("slug") or "")
    else:
        round_defects = list(st.get("defects") or [])

    # read prompt from compose for record
    best_doc = json.loads((REPO / "best_prompts_by_scale.json").read_text())
    prompt = compose_prompt_v2(bot, best_doc, r, defects=st.get("defects") if r >= 2 else None)

    rec = {
        "round": r,
        "filename": r_path.name,
        "prompt": prompt,
        "pad_src": (pad_src.name if pad_src is not None else None),
        "pad_mode": state["pad"],
        "bytes": conv.get("bytes"),
        "gen_engine": "cursor.GenerateImage",
        "source_image": str(src),
        "score_ok": score_ok,
        "total": total,
        "dims": dims,
        "defects": round_defects[:4],
        "grade": scored.get("grade") if score_ok else None,
        "score_fail_double": bool(scored.get("score_fail_double")),
    }

    sk = f"round::{stem}::r{r}"
    if score_ok:
        scores.setdefault("images", {})[sk] = scored
        scores.get("failures", {}).pop(sk, None)
    else:
        scores.setdefault("failures", {})[sk] = scored
    atomic_write_json(scores_path, scores)

    anat = anat_of(rec) if score_ok else None
    # Offline Absolute-5D fills perspective_anatomy with NEUTRAL_PRIOR=7.0 (N/A).
    # Treat that prior as non-blocking so early-stop / promote still work.
    backend = (state.get("score_backend") or "offline").lower()
    scored_backend = str(scored.get("score_backend") or "")
    offline_anat_na = (
        backend == "offline"
        or "offline" in scored_backend
        or scored.get("track") == "A_absolute_5d_offline_checklist"
    ) and anat is not None and abs(float(anat) - 7.0) < 1e-6
    if offline_anat_na:
        anat_ok = bool(score_ok)
        rec["anat_na_offline"] = True
    else:
        anat_ok = bool(score_ok and anat is not None and anat >= float(state["anat_gate"]))
    rec["anat_ok"] = anat_ok

    best_round = st.get("best_round")
    no_improve = int(st.get("no_improve") or 0)
    drop_streak = int(st.get("drop_streak") or 0)
    last_ok_total = st.get("last_ok_total")
    improved = False

    if total is not None:
        if best_round is None:
            best_round = rec
            no_improve = 0
            improved = True
        else:
            best_anat_ok = bool(best_round.get("anat_ok", True))
            best_total = float(best_round.get("total") or -1)
            if (anat_ok and not best_anat_ok) or (anat_ok == best_anat_ok and total > best_total):
                best_round = rec
                no_improve = 0
                improved = True
            elif score_ok:
                no_improve += 1

    min_r = int(st["min_rounds"])
    stop_reason = None
    threshold = float(state["threshold"])
    max_rounds = int(state["max_rounds"])
    pad_mode = state["pad"]
    ref = REPO / bot["ref_image"]

    # Early-stop: R1 >= 8.5 with anat ok (Grok v2 lever; overrides min_rounds)
    if (
        r == 1
        and total is not None
        and total >= float(EARLY_STOP_R1_GE)
        and anat_ok
    ):
        stop_reason = "STOP_EARLY_R1_GE_8_5"
        best_round = rec

    if stop_reason is None and total is not None and total >= threshold and anat_ok and r >= min_r:
        stop_reason = "STOP_TARGET_REACHED"
        best_round = rec
    elif stop_reason is None:
        if (
            float(state["drop_stop"]) > 0
            and total is not None
            and best_round is not None
            and best_round["round"] != r
            and float(best_round.get("total") or 0) - total > float(state["drop_stop"])
        ):
            drop_streak += 1
        elif score_ok:
            drop_streak = 0

        if (
            float(state["drop_stop"]) > 0
            and r >= int(state["early_stop_min_round"])
            and r >= min_r
            and drop_streak >= int(state["drop_streak"])
            and best_round is not None
        ):
            stop_reason = "STOP_DROP"

    # advance pad / defects if continuing
    next_pad = pad_src
    # Lever: if this round scored >= 8.2, force later pads back to style_ref
    force_ref_pad = bool(total is not None and total >= float(FORCE_REF_PAD_IF_R1_GE))
    # Round2: if THIS round is weak (<8.2), do NOT chain it as pad — snap to style_ref
    force_ref_weak = bool(total is not None and total < float(FORCE_REF_IF_TOTAL_LT))
    # Also honor any prior round that already crossed the bar
    if not force_ref_pad:
        for prev in (st.get("rounds") or []):
            try:
                if float(prev.get("total") or 0) >= float(FORCE_REF_PAD_IF_R1_GE) and prev.get("score_ok"):
                    force_ref_pad = True
                    break
            except (TypeError, ValueError):
                pass
    # ishtar always prefers style/web_ref pad (scene drift was Round1 killer)
    # Round3: bold/style_jump must NOT pad with source style_ref (medium fight)
    slug = bot.get("slug") or ""
    display = bot.get("display_scale") or ""
    mode = bot.get("prompt_mode") or ""
    is_bold = display == "recompose_bold" or mode == "style_jump"
    force_ref_slug = slug == "ishtar_canyon" and not is_bold
    if stop_reason is None and r < max_rounds:
        if not score_ok:
            next_pad = None if is_bold else ref
            # defects unchanged
        else:
            st["defects"] = list(round_defects[:2])
            if is_bold:
                # free medium jump — no style_ref pad; optional previous if strong
                if (
                    anat_ok
                    and total is not None
                    and total >= float(FORCE_REF_PAD_IF_R1_GE)
                    and improved
                ):
                    next_pad = r_path
                    rec["pad_force_ref"] = False
                    rec["pad_force_ref_reason"] = "bold_chain_strong_prev"
                else:
                    next_pad = None
                    rec["pad_force_ref"] = False
                    rec["pad_force_ref_reason"] = "bold_no_style_ref_pad"
            elif force_ref_weak or force_ref_slug or force_ref_pad or pad_mode == "ref":
                next_pad = ref
                rec["pad_force_ref"] = True
                if force_ref_weak:
                    rec["pad_force_ref_reason"] = "weak_total_lt_8_2"
                elif force_ref_slug:
                    rec["pad_force_ref_reason"] = "ishtar_scene_lock"
            elif pad_mode == "previous":
                next_pad = r_path
            else:  # auto — only chain previous when strong (>=8.2) AND non-decreasing
                if (
                    anat_ok
                    and total is not None
                    and total >= float(FORCE_REF_PAD_IF_R1_GE)
                    and (
                        (last_ok_total is not None and total >= last_ok_total)
                        or improved
                    )
                ):
                    next_pad = r_path
                else:
                    next_pad = ref
            if total is not None and anat_ok:
                last_ok_total = total
    elif stop_reason is None and r >= max_rounds:
        stop_reason = "max_rounds_reached"

    rounds = list(st.get("rounds") or [])
    rounds.append(rec)
    st["rounds"] = rounds
    st["best_round"] = best_round
    st["no_improve"] = no_improve
    st["drop_streak"] = drop_streak
    st["last_ok_total"] = last_ok_total
    st["pad_src"] = str(next_pad) if next_pad is not None else None

    if stop_reason:
        st["status"] = "done"
        st["stop_reason"] = stop_reason
        st["next_round"] = r  # finished at this round
        # promote best to final
        if best_round is None:
            best_round = rounds[-1]
            st["best_round"] = best_round
        best_src = out_dir / best_round["filename"]
        final_path = out_dir / f"{stem}.jpg"
        if best_src.is_file():
            shutil.copy2(best_src, final_path)
        final_score = float(best_round.get("total") or 0) if best_round.get("score_ok") else None
        bot_score_key = f"bot::{final_path.name}"
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

        anat_val = anat_of(best_round)
        reached = (
            final_score is not None
            and final_score >= threshold
            and anat_val is not None
            and anat_val >= float(state["anat_gate"])
        )
        reached_anat_85 = (
            final_score is not None
            and final_score >= threshold
            and (anat_val is not None and anat_val >= 8.5)
        )
        item = {
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
            "pad_mode": pad_mode,
            "display_scale": bot["display_scale"],
            "api_scale": bot["api_scale"],
            "slug": bot["slug"],
            "prompt_mode": bot.get("prompt_mode"),
            "aspect_ratio": bot.get("aspect_ratio"),
            "gen_engine": "cursor.GenerateImage",
            "rounds": rounds,
        }
        manifest = load_json(out_dir / "gen_manifest.json", {"items": {}})
        manifest["items"][bid] = item
        atomic_write_json(out_dir / "gen_manifest.json", manifest)
    else:
        st["next_round"] = r + 1
        st["status"] = "active"

    state["bots"][bid] = st
    state["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    atomic_write_json(state_path, state)

    print(json.dumps({
        "ok": True,
        "bot_id": bid,
        "round": r,
        "total": total,
        "anat": anat,
        "anat_ok": anat_ok,
        "status": st["status"],
        "stop_reason": st.get("stop_reason"),
        "next_round": st.get("next_round"),
        "next_pad": (Path(st["pad_src"]).name if st.get("pad_src") else None),
        "defects": st.get("defects"),
        "out": str(r_path),
    }, ensure_ascii=False))
    return 0


def mark_failed(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    state = load_json(out_dir / STATE_NAME, None)
    if not state:
        print(json.dumps({"ok": False, "error": "no state"}))
        return 1
    st = state["bots"].get(args.bot_id)
    if not st:
        print(json.dumps({"ok": False, "error": "unknown bot"}))
        return 1
    st["status"] = "failed"
    st["error"] = args.error or "GenerateImage failed"
    st["stop_reason"] = "GEN_FAIL"
    state["bots"][args.bot_id] = st
    atomic_write_json(out_dir / STATE_NAME, state)
    manifest = load_json(out_dir / "gen_manifest.json", {"items": {}})
    manifest["items"][args.bot_id] = {
        "bot_id": args.bot_id,
        "ok": False,
        "error": st["error"],
        "rounds": st.get("rounds") or [],
        "gen_engine": "cursor.GenerateImage",
    }
    atomic_write_json(out_dir / "gen_manifest.json", manifest)
    print(json.dumps({"ok": True, "bot_id": args.bot_id, "failed": True}, ensure_ascii=False))
    return 0


def finalize(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    state = load_json(out_dir / STATE_NAME, {})
    manifest = load_json(out_dir / "gen_manifest.json", {"items": {}})
    # ensure all done bots are in manifest
    for bid, st in (state.get("bots") or {}).items():
        if st.get("status") == "done" and bid not in manifest.get("items", {}):
            # reconstruct minimal
            best_round = st.get("best_round")
            if not best_round:
                continue
            bot = st["bot"]
            stem = st["stem"]
            final_path = out_dir / f"{stem}.jpg"
            if best_round and (out_dir / best_round["filename"]).is_file() and not final_path.is_file():
                shutil.copy2(out_dir / best_round["filename"], final_path)
            final_score = float(best_round.get("total") or 0) if best_round.get("score_ok") else None
            anat_val = anat_of(best_round)
            reached = (
                final_score is not None
                and final_score >= float(state.get("threshold") or 9.6)
                and anat_val is not None
                and anat_val >= float(state.get("anat_gate") or 7.5)
            )
            manifest.setdefault("items", {})[bid] = {
                "bot_id": bid,
                "ok": True,
                "final": str(final_path),
                "final_filename": final_path.name,
                "final_score": final_score,
                "final_dims": best_round.get("dims") or {},
                "best_round": best_round["round"],
                "n_rounds": len(st.get("rounds") or []),
                "stop_reason": st.get("stop_reason"),
                "reached_threshold": bool(reached),
                "gen_engine": "cursor.GenerateImage",
                "display_scale": bot["display_scale"],
                "slug": bot["slug"],
                "rounds": st.get("rounds") or [],
            }
    atomic_write_json(out_dir / "gen_manifest.json", manifest)

    results = list(manifest.get("items", {}).values())
    ok = [r for r in results if r.get("ok")]
    fail = [r for r in results if not r.get("ok")]
    reached = [r for r in ok if r.get("reached_threshold")]
    scored_ok = [r for r in ok if isinstance(r.get("final_score"), (int, float))]
    threshold = float(state.get("threshold") or 9.6)
    anat_gate = float(state.get("anat_gate") or 7.5)
    summary = {
        "version": "v8_20_skill_grok_v2",
        "threshold": threshold,
        "anat_gate": anat_gate,
        "max_rounds": state.get("max_rounds", 8),
        "pad": state.get("pad", "auto"),
        "gen_engine": "cursor.GenerateImage",
        "n_ok": len(ok),
        "n_fail": len(fail),
        "n_reached_9_60": len(reached),
        "n_reached_9_60_and_anat_8_5": sum(
            1 for r in ok
            if (r.get("final_score") or 0) >= threshold
            and ((r.get("final_dims") or {}).get("perspective_anatomy") or 0) >= 8.5
        ),
        "mean_final": round(sum(float(r["final_score"]) for r in scored_ok) / len(scored_ok), 3) if scored_ok else None,
        "min_final": round(min(float(r["final_score"]) for r in scored_ok), 3) if scored_ok else None,
        "max_final": round(max(float(r["final_score"]) for r in scored_ok), 3) if scored_ok else None,
        "round_dist": dict(Counter(int(r.get("n_rounds") or 0) for r in ok)),
        "stop_reasons": dict(Counter(str(r.get("stop_reason")) for r in ok)),
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
        "compare": {
            "gpt_image_v2fix_mean": 8.94,
            "oct26_backup_mean": 9.14,
        },
    }
    atomic_write_json(out_dir / "SCORE_SUMMARY.json", summary)
    md = [
        "# V8-20 skill converge Grok (GenerateImage) summary",
        f"- gen: **cursor.GenerateImage** · score: offline Absolute-5D (gpt-6-sol VLM skipped: INSUFFICIENT_BALANCE) · threshold ≥{threshold} · anat≥{anat_gate} · max {state.get('max_rounds',8)} · pad={state.get('pad','auto')} · levers: ref_if_R1≥8.2 / soft_recompose / anat+micro locks / early_R1≥8.5",
        f"- ok: {len(ok)}/{len(results)} · reached≥9.60: **{len(reached)}** · mean: {summary['mean_final']} · range: {summary['min_final']}–{summary['max_final']}",
        f"- vs gpt-image v2fix mean 8.94 · vs oct26 backup mean 9.14",
        f"- round_dist: {summary['round_dist']}",
        f"- stop_reasons: {summary['stop_reasons']}",
        "",
        "## Not reached",
    ]
    for row in summary["not_reached"]:
        md.append(f"- {row['bot_id']}: score={row['score']} anat={row['anat']} stop={row['stop']} rounds={row['n_rounds']}")
    if fail:
        md.append("\n## Failures")
        for f in fail:
            md.append(f"- {f.get('bot_id')}: {f.get('error')}")
    (out_dir / "SCORE_SUMMARY.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # also write bot-level SCORE_SUMMARY bot block like previous for HTML builder
    bot_block = {
        "bot": {
            "n": len(scored_ok),
            "mean": summary["mean_final"],
            "min": summary["min_final"],
            "max": summary["max_final"],
            "ge_9_6": summary["n_reached_9_60"],
            "ge_9_0": sum(1 for r in scored_ok if float(r["final_score"]) >= 9.0),
            "ge_8_5": sum(1 for r in scored_ok if float(r["final_score"]) >= 8.5),
        },
        "converge": {
            "total": len(ok),
            "ok": len(ok),
            "fail": len(fail),
            "mean": summary["mean_final"],
            "min": summary["min_final"],
            "max": summary["max_final"],
            "reached_threshold": summary["n_reached_9_60"],
            "round_dist": summary["round_dist"],
            "stop_reasons": summary["stop_reasons"],
        },
        **summary,
    }
    atomic_write_json(out_dir / "SCORE_SUMMARY.json", bot_block)

    print(json.dumps({"ok": True, "summary": summary}, ensure_ascii=False, indent=2))
    return 0 if not fail else 1


def status(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    state = load_json(out_dir / STATE_NAME, {})
    rows = []
    for bid, st in (state.get("bots") or {}).items():
        br = st.get("best_round") or {}
        rows.append({
            "bot_id": bid,
            "status": st.get("status"),
            "next_round": st.get("next_round"),
            "best_total": br.get("total"),
            "stop": st.get("stop_reason"),
            "n_rounds": len(st.get("rounds") or []),
            "error": st.get("error"),
        })
    print(json.dumps({
        "ok": True,
        "counts": Counter(r["status"] for r in rows),
        "bots": rows,
    }, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("init", "next-jobs", "ingest", "finalize", "status", "mark-failed"))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--env", default="/home/box/.config/pmem-art/apikey_fan.env")
    ap.add_argument("--score-model", default="gpt-6-sol")
    ap.add_argument("--score-backend", choices=("auto", "vlm", "offline"), default="offline",
                    help="offline=Absolute-5D checklist; vlm=gpt-6-sol; auto=vlm then offline on balance fail")
    ap.add_argument("--threshold", type=float, default=9.6)
    ap.add_argument("--anat-gate", type=float, default=7.5)
    ap.add_argument("--max-rounds", type=int, default=8)
    ap.add_argument("--pad", choices=("ref", "previous", "auto"), default="auto")
    ap.add_argument("--drop-stop", type=float, default=0.5)
    ap.add_argument("--early-stop-min-round", type=int, default=4)
    ap.add_argument("--drop-streak", type=int, default=2)
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--limit", type=int, default=4, help="next-jobs batch size")
    ap.add_argument("--limit-bots", type=int, default=0)
    ap.add_argument("--only", default="")
    ap.add_argument("--bot-id", default="")
    ap.add_argument("--round", type=int, default=0)
    ap.add_argument("--image", default="")
    ap.add_argument("--error", default="")
    args = ap.parse_args()

    if args.command == "init":
        return init_state(args)
    if args.command == "next-jobs":
        return next_jobs(args)
    if args.command == "ingest":
        return ingest(args)
    if args.command == "finalize":
        return finalize(args)
    if args.command == "status":
        return status(args)
    if args.command == "mark-failed":
        return mark_failed(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
