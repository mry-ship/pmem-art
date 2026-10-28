#!/usr/bin/env python3
"""Skill-contract loop for the V8 20.

Scoring priority: VLM (independent / quant) → Agent manual record → offline advisory only.
Generation: apikey.fan first; on balance error emit cursor.GenerateImage job spec.

Stop only at weighted >= 9.6 after min rounds, anatomy gate, R4+ drop-stop, or round 8.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from run_v8_20_skill_converge_v2fix import compose_prompt, load_env, min_rounds_for, select_bots  # noqa: E402
from skills_kit.converge_judge_bridge import score_for_converge  # noqa: E402
from skills_kit.skill_image_gen import fan_or_generate_image_job  # noqa: E402
from skills_kit import get_converge_scale_profile  # noqa: E402

DIMS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
)
WEIGHTS = {
    "low": {"composition": 0.15, "lighting_color": 0.20, "perspective_anatomy": 0.25, "texture_detail": 0.25, "spec_style": 0.15},
    "medium": {"composition": 0.20, "lighting_color": 0.25, "perspective_anatomy": 0.20, "texture_detail": 0.20, "spec_style": 0.15},
    "high": {"composition": 0.15, "lighting_color": 0.30, "perspective_anatomy": 0.15, "texture_detail": 0.20, "spec_style": 0.20},
    "recompose": {"composition": 0.30, "lighting_color": 0.20, "perspective_anatomy": 0.20, "texture_detail": 0.15, "spec_style": 0.15},
}
STATE_NAME = "look_state.json"


def weighted(dims: dict, api: str) -> float:
    w = WEIGHTS.get(api, {k: 0.2 for k in DIMS})
    return round(sum(float(dims[k]) * w[k] for k in DIMS), 2)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def init(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    doc = json.loads((REPO / "bot_tasks_v8.json").read_text(encoding="utf-8"))
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    bots = {}
    for b in select_bots(doc):
        ref = str((REPO / b["ref_image"]).resolve())
        bold = b.get("display_scale") == "recompose_bold" or b.get("prompt_mode") == "style_jump"
        bots[b["bot_id"]] = {
            "bot": b,
            "status": "active",
            "next_round": 1,
            "pad_src": None if bold else ref,
            "defects": [],
            "rounds": [],
            "best_round": None,
            "drop_streak": 0,
            "stop_reason": None,
            "min_rounds": min_rounds_for(b),
            "best_doc_used": True,
        }
        bots[b["bot_id"]]["r1_prompt"] = compose_prompt(b, best, 1)
    state = {
        "version": "skill_look_rerun",
        "threshold": 9.6,
        "anat_gate": 7.5,
        "max_rounds": 8,
        "judge": "agent_look",
        "bots": bots,
    }
    save(out / STATE_NAME, state)
    print(f"init {len(bots)} -> {out}")


def next_jobs(out: Path, limit: int) -> None:
    state = load(out / STATE_NAME)
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    jobs = []
    for bid, st in state["bots"].items():
        if st.get("status") != "active":
            continue
        r = int(st["next_round"])
        if r > 8:
            continue
        bot = st["bot"]
        prompt = compose_prompt(bot, best, r, defects=st.get("defects") if r >= 2 else None)
        jobs.append({
            "bot_id": bid,
            "round": r,
            "slug": bot["slug"],
            "scale": bot["display_scale"],
            "aspect_ratio": bot.get("aspect_ratio") or "1:1",
            "pad_src": st.get("pad_src"),
            "prompt": prompt,
            "gen_filename": f"{bid}_r{r}.png",
        })
        if len(jobs) >= limit:
            break
    print(json.dumps(jobs, ensure_ascii=False, indent=2))


def record(out: Path, bot_id: str, round_num: int, image: str, dims: dict, defects: list[str]) -> None:
    state = load(out / STATE_NAME)
    st = state["bots"][bot_id]
    bot = st["bot"]
    if int(st["next_round"]) != round_num or st["status"] != "active":
        raise SystemExit(f"unexpected {bot_id} want R{st['next_round']} got R{round_num} {st['status']}")
    for k in DIMS:
        dims[k] = round(float(dims[k]), 1)
    api = bot.get("api_scale") or "medium"
    if bot.get("display_scale") == "recompose_bold":
        api = "recompose"
    total = weighted(dims, api if api in WEIGHTS else "medium")
    anat = float(dims["perspective_anatomy"])
    anat_ok = anat >= 7.5
    rec = {"round": round_num, "image": image, "dims": dims, "total": total, "defects": defects[:2], "anat_ok": anat_ok}
    st["rounds"].append(rec)
    st["rounds"].append(rec)
    best = st.get("best_round")
    if best is None or (anat_ok and not best.get("anat_ok")) or (anat_ok == best.get("anat_ok") and total > best["total"]):
        st["best_round"] = rec
    best = st["best_round"]
    stop = None
    if total >= 9.6 and anat_ok and round_num >= int(st["min_rounds"]):
        stop = "STOP_TARGET_REACHED"
        st["best_round"] = rec
    elif round_num >= 4 and best and best["round"] != round_num and best["total"] - total > 0.5:
        st["drop_streak"] = int(st.get("drop_streak") or 0) + 1
        if st["drop_streak"] >= 2 and round_num >= int(st["min_rounds"]):
            stop = "STOP_DROP"
    else:
        st["drop_streak"] = 0
    if stop is None and round_num >= 8:
        stop = "max_rounds_reached"
    if stop:
        st["status"] = "done"
        st["stop_reason"] = stop
    else:
        st["defects"] = defects[:2]
        st["next_round"] = round_num + 1
        # low/medium/high/recompose always pad the original ref. Style jump pads nothing.
        bold = bot.get("display_scale") == "recompose_bold"
        ref = str((REPO / bot["ref_image"]).resolve())
        st["pad_src"] = None if bold else ref
    st["rounds"][-1] = rec
    save(out / STATE_NAME, state)
    print(json.dumps({"bot_id": bot_id, "round": round_num, "total": total, "anat": anat, "status": st["status"], "stop": st.get("stop_reason"), "next": st.get("next_round"), "fixes": st.get("defects")}, ensure_ascii=False))


def try_gen(out: Path, bot_id: str, assets_dir: Path) -> None:
    state = load(out / STATE_NAME)
    st = state["bots"][bot_id]
    bot = st["bot"]
    r = int(st["next_round"])
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    prompt = compose_prompt(bot, best, r, defects=st.get("defects") if r >= 2 else None)
    ar = bot.get("aspect_ratio") or "1:1"
    out_path = assets_dir / f"{bot_id}_r{r}.jpg"
    pad = Path(st["pad_src"]) if st.get("pad_src") else None
    res = fan_or_generate_image_job(
        prompt=prompt,
        out_path=out_path,
        pad_src=pad,
        aspect_ratio=ar,
        bot_id=bot_id,
        round_num=r,
    )
    print(json.dumps(res, ensure_ascii=False, indent=2))


def try_vlm_record(out: Path, bot_id: str, image: str, env_path: Path) -> None:
    """Score with VLM bridge; if ok, record. If agent pending, print hint only."""
    state = load(out / STATE_NAME)
    st = state["bots"][bot_id]
    bot = st["bot"]
    r = int(st["next_round"])
    env = load_env(env_path)
    scale_prof = get_converge_scale_profile(
        str(bot.get("api_scale") or "medium"),
        goal=bot.get("goal") or "",
        ref_image=bot.get("ref_image") or "",
    )
    item = {
        "path": image,
        "bot_id": bot_id,
        "round": r,
        "api_scale": bot.get("api_scale") or "medium",
        "ref_image": bot.get("ref_image") or "",
        "goal": bot.get("goal") or "",
    }
    scored = score_for_converge(item, env, "gpt-6-sol", root=REPO, scale_prof=scale_prof, goal=bot.get("goal") or "")
    if scored.get("ok"):
        dims = scored.get("dims") or {}
        defects = scored.get("defects") or []
        record(out, bot_id, r, image, dims, defects)
        return
    print(json.dumps({"ok": False, "judge_pending": scored.get("judge_pending"), "error": scored.get("error")}, ensure_ascii=False, indent=2))


def build_html(out: Path) -> None:
    from build_skill_look_board import build  # noqa: WPS433

    build(out / STATE_NAME, REPO / "docs" / "showcase" / "skill_look_20" / "index.html")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("init", "next", "record", "status", "gen", "judge", "build-html"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--bot")
    ap.add_argument("--round", type=int)
    ap.add_argument("--image")
    ap.add_argument("--dims")
    ap.add_argument("--defects")
    ap.add_argument("--assets", default=str(Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")))
    ap.add_argument("--env", default=str(REPO / ".local" / "apikey_fan.env"))
    args = ap.parse_args()
    out = Path(args.out)
    if args.cmd == "init":
        init(out)
        return 0
    if args.cmd == "next":
        next_jobs(out, args.limit)
        return 0
    if args.cmd == "gen":
        if not args.bot:
            raise SystemExit("--bot required")
        try_gen(out, args.bot, Path(args.assets))
        return 0
    if args.cmd == "judge":
        if not args.bot or not args.image:
            raise SystemExit("--bot and --image required")
        try_vlm_record(out, args.bot, args.image, Path(args.env))
        return 0
    if args.cmd == "build-html":
        build_html(out)
        return 0
    if args.cmd == "status":
        state = load(out / STATE_NAME)
        for bid, st in state["bots"].items():
            best = (st.get("best_round") or {}).get("total")
            print(f"{bid} {st['status']} R{len(st['rounds'])} next={st['next_round']} best={best} {st.get('stop_reason') or ''}")
        return 0
    dims = json.loads(args.dims)
    defects = json.loads(args.defects)
    record(out, args.bot, args.round, args.image, dims, defects)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
