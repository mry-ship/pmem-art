#!/usr/bin/env python3
"""Same-scope 1029 rerun: 4 rounds or >= 9.5 per scored cell. Does not touch 1028."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from skills_kit.converge_loop import clear_active_session  # noqa: E402
from skills_kit.showcase_gate import can_accept_winner  # noqa: E402

IMAGE_GEN = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-image\image_gen.py")
GPT = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\gpt.py")
OLD = REPO / "docs" / "showcase" / "homepage_rerun_1028"
OUT = REPO / "docs" / "showcase" / "homepage_rerun_1029"
PY = sys.executable
WORKERS = 3
MAX_ROUNDS = 4
TH = 9.5
SIZE = {
    "9:16": "1024x1536",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
    "1:1": "1024x1024",
}

C01 = "docs/showcase/homepage_rerun_1028/draw_matrix/c01/ref.jpg"
C02 = "docs/showcase/homepage_rerun_1028/draw_matrix/c02/ref.jpg"
C03 = "docs/showcase/homepage_rerun_1028/draw_matrix/c03/ref.jpg"
C04 = "docs/showcase/homepage_rerun_1028/draw_matrix/c04/ref.jpg"
EXPR = "docs/showcase/homepage_rerun_1028/v2/variant_expr/ref.jpg"

C01_LOCK = (
    "9:16 epic night city from a ridge. Pale-robe dark-hair swordsman on CHARCOAL WET dark roof tiles, "
    "not green glaze. Warm WINDOW FIRE lights in the city below, cool fog, planetary limb at top. "
    "No lantern as key light, no starfield replacing the city, no neon."
)
C02_LOCK = (
    "4:3 oil-pastel crayon paper. Black bob, red hoodie, blue shorts, BOTH legs over-knee BLACK socks, "
    "near thigh of the closer leg bare above the sock, white sneakers with black stripes. "
    "Diagonal blue-grey crayon background, blush air. No ankle socks, no missing sock, no extra limbs."
)
C03_LOCK = (
    "3:4 window portrait. NEAR-BLACK hair (ink black with only cool window sheen, NOT blue or teal dye). "
    "Light blue eyes, white cat clip, black over-ear headphones, loose white tee, warm gold window light "
    "and leaf shadows, white cosmos flowers. Commercial anime paint."
)
C04_LOCK = (
    "4:3 ink-and-wash courtyard well looking UP. Ochre/honey/amber brick, readable ink lines, "
    "broken wooden stairs, warm light. NOT charcoal grayscale, NOT a spiral staircase as the whole well."
)


def jobs() -> list[dict]:
    draw = []
    rec = {
        "c01": "Stand in the central long street looking up at roof ridges; the swordsman becomes a small silhouette on a ridge; fog separates street from the window-fire sea. Keep charcoal wet tiles and window fire.",
        "c02": "Same pastel girl, side half-body, still over-knee black socks, red hoodie, crayon paper.",
        "c03": "Three-quarter back view, face still looking at the window. Keep near-black hair, cat clip, headphones, white tee, cosmos.",
        "c04": "From the well mouth looking down into the same ochre courtyard, broken stairs, ink wash.",
    }
    for cid, ar, module, lock, ref in (
        ("c01", "9:16", "scene.NightCity", C01_LOCK, C01),
        ("c02", "4:3", "character.PastelHoodie", C02_LOCK, C02),
        ("c03", "3:4", "character.SunlitGirl", C03_LOCK, C03),
        ("c04", "4:3", "scene.CourtWell", C04_LOCK, C04),
    ):
        for scale, extra in (
            ("low", "Only repair one local flaw. Keep camera, pose, identity."),
            ("medium", "Small polish, lock camera and identity."),
            ("high", "Bolder lighting and finish, keep identity."),
            ("recompose", rec[cid]),
        ):
            draw.append(
                {
                    "id": f"{cid}_{scale}",
                    "skill": "draw",
                    "module": module,
                    "scale": scale,
                    "aspect_ratio": ar,
                    "ref": ref,
                    "analysis": lock,
                    "goal": f"{lock} Scale={scale}. {extra}",
                    "rel_dir": f"draw_matrix/{cid}/{scale}",
                    "family": "art",
                }
            )
    extras = [
        {
            "id": "clone_kite",
            "skill": "clone",
            "module": "character.KiteBoy",
            "scale": "medium",
            "aspect_ratio": "4:3",
            "ref": C02,
            "analysis": "Lock only crayon paper tooth and blush air. Do not copy the girl.",
            "goal": "New subject: short-hair boy sitting on stone steps holding a rolled paper kite. Keep oil-pastel paper. Not the red-hoodie girl.",
            "rel_dir": "v2/clone",
            "family": "art",
        },
        {
            "id": "clone_rabbit",
            "skill": "clone",
            "module": "character.PastelRabbit",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": C02,
            "analysis": "Lock crayon paper and blush air only.",
            "goal": "White rabbit hugging a carrot, new composition, pastel crayon paper, no cyber neon, not the hoodie girl.",
            "rel_dir": "v2/clone_rabbit",
            "family": "art",
        },
        {
            "id": "variant_light",
            "skill": "variant",
            "module": "character.SunlitGirl",
            "scale": "medium",
            "aspect_ratio": "3:4",
            "ref": C03,
            "analysis": C03_LOCK,
            "goal": "Same window girl identity and camera. Stronger hair translucency, skin SSS, dust motes, warm gold rim. Do not change outfit, headphones, cat clip, or dye the hair blue.",
            "rel_dir": "v2/variant",
            "family": "art",
        },
        {
            "id": "variant_surprise",
            "skill": "variant",
            "module": "character.SunlitGirl",
            "scale": "medium",
            "aspect_ratio": "3:4",
            "ref": EXPR,
            "analysis": C03_LOCK,
            "goal": "Same identity and camera. ONLY surprised open mouth showing upper teeth. Near-black hair stays.",
            "rel_dir": "v2/variant_expr",
            "family": "art",
        },
        {
            "id": "variant_wink",
            "skill": "variant",
            "module": "character.SunlitGirl",
            "scale": "medium",
            "aspect_ratio": "3:4",
            "ref": EXPR,
            "analysis": C03_LOCK,
            "goal": "Same identity and camera. ONLY a playful wink. Near-black hair stays.",
            "rel_dir": "v2/variant_wink",
            "family": "art",
        },
        {
            "id": "variant_sleepy",
            "skill": "variant",
            "module": "character.SunlitGirl",
            "scale": "medium",
            "aspect_ratio": "3:4",
            "ref": EXPR,
            "analysis": C03_LOCK,
            "goal": "Same identity and camera. ONLY sleepy half-lidded eyes. Near-black hair stays.",
            "rel_dir": "v2/variant_sleepy",
            "family": "art",
        },
        {
            "id": "variant_angry",
            "skill": "variant",
            "module": "character.SunlitGirl",
            "scale": "medium",
            "aspect_ratio": "3:4",
            "ref": EXPR,
            "analysis": C03_LOCK,
            "goal": "Same identity and camera. ONLY a slight pout, mildly angry. Near-black hair stays.",
            "rel_dir": "v2/variant_angry",
            "family": "art",
        },
        {
            "id": "ui_royal",
            "skill": "ui",
            "module": "ui.RoyalGardenHome",
            "scale": "high",
            "aspect_ratio": "9:16",
            "ref": "",
            "analysis": "Do not pad a screenshot. Candy-glaze casual match-3 home, 9:16.",
            "goal": (
                "9:16 casual match-3 HOME SCREEN, not a match board. Butter-yellow greenhouse fills the screen: "
                "arch windows, plant shelves, red velvet sofa, tea set, gold watering can, lemon tree, blue rug "
                "and a small yellow round rug. UI overlay: coin 2860, infinite hearts, 01:12:05, stars 6, "
                "watering-can progress 120/500 x3, three round left badges (flower/teacup/sun), gold bell, "
                "Garden 12 and Room 3, Home tab. Glazed candy buttons, champagne gold bevel, no garbage text, no neon."
            ),
            "rel_dir": "v2/ui_royal/portrait",
            "family": "ui",
        },
        {
            "id": "icon_a_city",
            "skill": "icon.a",
            "module": "icon.AppCity",
            "scale": "high",
            "aspect_ratio": "1:1",
            "ref": "",
            "analysis": "Mode A 1024 full-bleed square, single glyph.",
            "goal": "1024 app icon, full-bleed RIGHT-ANGLE square, no round-corner mask, no 3:4 poster, no scene illustration. Indigo field, ONE floating city plus moon disc inside 75 percent safe zone, tiny gold stars, tactile micro-bevel, NO letters.",
            "rel_dir": "v2/icon_a",
            "family": "icon.a",
        },
        {
            "id": "icon_a_coin",
            "skill": "icon.a",
            "module": "icon.AppCoin",
            "scale": "high",
            "aspect_ratio": "1:1",
            "ref": "",
            "analysis": "Mode A 1024 full-bleed square.",
            "goal": "1024 app icon, full-bleed square, no text. One celadon-glaze gold coin glyph, wet highlight stripe, 75 percent safe zone, not an illustration.",
            "rel_dir": "v2/icon_a2",
            "family": "icon.a",
        },
        {
            "id": "icon_a_forge",
            "skill": "icon.a",
            "module": "icon.AppForge",
            "scale": "high",
            "aspect_ratio": "1:1",
            "ref": "",
            "analysis": "Mode A 1024 full-bleed square.",
            "goal": "1024 app icon, full-bleed square, no text. One hammer-and-anvil glyph with ember glow, 75 percent safe zone, not a forge scene.",
            "rel_dir": "v2/icon_a3",
            "family": "icon.a",
        },
        {
            "id": "icon_c_heal",
            "skill": "icon.c",
            "module": "icon.PropHeal",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": "",
            "transparent": True,
            "analysis": "Mode C item icon.",
            "goal": "Game item icon, thick silhouette, studio light, vignette, no text. Red healing potion, cork, readable glass, centered.",
            "rel_dir": "v2/icon_c_set",
            "stem": "heal",
            "family": "icon.c",
        },
        {
            "id": "icon_c_mana",
            "skill": "icon.c",
            "module": "icon.PropMana",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": "",
            "transparent": True,
            "analysis": "Mode C item icon.",
            "goal": "Game item icon, thick silhouette, studio light, vignette, no text. Blue mana potion, cork, centered.",
            "rel_dir": "v2/icon_c_set",
            "stem": "mana",
            "family": "icon.c",
        },
        {
            "id": "icon_c_key",
            "skill": "icon.c",
            "module": "icon.PropKey",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": "",
            "transparent": True,
            "analysis": "Mode C item icon.",
            "goal": "Game item icon, thick silhouette, studio light, vignette, no text. Warm metal antique key, readable teeth, centered.",
            "rel_dir": "v2/icon_c_set",
            "stem": "key",
            "family": "icon.c",
        },
        {
            "id": "icon_c_ruby",
            "skill": "icon.c",
            "module": "icon.PropRuby",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": "",
            "transparent": True,
            "analysis": "Mode C item icon.",
            "goal": "Game item icon, thick silhouette, studio light, vignette, no text. Faceted ruby, hard speculars, centered.",
            "rel_dir": "v2/icon_c_set",
            "stem": "ruby",
            "family": "icon.c",
        },
        {
            "id": "icon_c_scroll",
            "skill": "icon.c",
            "module": "icon.PropScroll",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": "",
            "transparent": True,
            "analysis": "Mode C item icon.",
            "goal": "Game item icon, thick silhouette, studio light, vignette, no text. Rolled parchment with red wax seal, centered, no readable writing.",
            "rel_dir": "v2/icon_c_set",
            "stem": "scroll",
            "family": "icon.c",
        },
    ]
    potion = [
        ("L01", "empty short cut-glass potion bottle, no cork, no liquid, occupies most of the square"),
        ("L02", "same short cut-glass bottle with cork, still empty"),
        ("L03", "corked bottle half filled with warm green healing liquid"),
        ("L04", "corked bottle full of green healing liquid"),
        ("L05", "full green potion with paper tag ring and a leaf on the neck"),
        ("L06", "tagged potion with a SMALL gold foot attached to the bottle itself, not a wooden table or tray"),
        ("L07", "same family short bottle, gold foot, crystal crown sitting on the cork"),
        ("L08", "largest divine bottle, crystal crown plus a halo rim"),
    ]
    candy = [
        ("L01", "small peach gummy candy, no wrapper, occupies most of the square"),
        ("L02", "fatter peach gummy, still one candy, no wrapper"),
        ("L03", "fat peach gummy with frosting grown on the candy surface, no wrapper"),
        ("L04", "frosted peach candy with a leaf growing out of the candy, not a separate plant"),
        ("L05", "leafed peach candy with a gem embedded in the candy"),
        ("L06", "peach candy with a small crown growing on the candy, no tray, no ribbon, no paper cup"),
        ("L07", "crowned peach candy with star points on the crown"),
        ("L08", "largest divine peach candy with a crown halo"),
    ]
    merge = []
    for code, desc in potion:
        merge.append(
            {
                "id": f"potion_{code}",
                "skill": "merge",
                "module": "prop.HealPotionMerge",
                "scale": "medium",
                "aspect_ratio": "1:1",
                "ref": "",
                "analysis": "One object, gray studio, contact shadow only, no wood tray.",
                "goal": f"Square game merge item. Single object centered. Cut-glass cartoon potion family. Gray empty studio, only a contact shadow. No table, no crate. {desc}. No face, no rank text.",
                "rel_dir": "v2/merge_potion_l16",
                "stem": code,
                "family": "icon.c",
            }
        )
    for code, desc in candy:
        merge.append(
            {
                "id": f"candy_{code}",
                "skill": "merge",
                "module": "prop.PeachCandyMerge",
                "scale": "medium",
                "aspect_ratio": "1:1",
                "ref": "",
                "analysis": "Parts grow on the candy. No packaging chain.",
                "goal": f"Square game merge item. Single object centered. Soft peach gummy family. Empty studio, contact shadow only. Occupies most of the cell. {desc}. No wrapper, no sticker sheet, no paper cup, no ribbon, no tray. No face, no rank text.",
                "rel_dir": "v2/merge_candy_l16",
                "stem": code,
                "family": "icon.c",
            }
        )
    merge.append(
        {
            "id": "merge_t5",
            "skill": "merge",
            "module": "prop.HealPotionMerge",
            "scale": "medium",
            "aspect_ratio": "1:1",
            "ref": "",
            "analysis": "T5 is the crystal-crown bottle, same short-bottle family.",
            "goal": "Square product shot, crystal-crown potion, cut glass, crown on the cork of the same short bottle, gray studio, contact shadow, no picture frame, no table, no face, no rank text.",
            "rel_dir": "v2/merge",
            "stem": "final",
            "family": "icon.c",
        }
    )
    return draw + extras + merge


def run(cmd: list[str], timeout: int = 420) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(REPO),
        capture_output=True,
        text=True,
        timeout=timeout,
        encoding="utf-8",
        errors="replace",
    )


def pmem(*args: str) -> subprocess.CompletedProcess[str]:
    return run([PY, str(REPO / "pmem_art.py"), *args], timeout=180)


def copy_static() -> None:
    pairs = [
        ("draw_matrix/c01/ref.jpg", "draw_matrix/c01/ref.jpg"),
        ("draw_matrix/c02/ref.jpg", "draw_matrix/c02/ref.jpg"),
        ("draw_matrix/c03/ref.jpg", "draw_matrix/c03/ref.jpg"),
        ("draw_matrix/c04/ref.jpg", "draw_matrix/c04/ref.jpg"),
        ("v2/clone_rabbit/ref.jpg", "v2/clone_rabbit/ref.jpg"),
        ("v2/variant_expr/ref.jpg", "v2/variant_expr/ref.jpg"),
        ("v2/style_lock_b/ref1.jpg", "v2/style_lock_b/ref1.jpg"),
        ("v2/style_lock_b/ref2.jpg", "v2/style_lock_b/ref2.jpg"),
        ("v2/style_lock_b/final.jpg", "v2/style_lock_b/final.jpg"),
        ("v2/style_lock_c/ref1.jpg", "v2/style_lock_c/ref1.jpg"),
        ("v2/style_lock_c/ref2.jpg", "v2/style_lock_c/ref2.jpg"),
        ("v2/style_lock_c/final.jpg", "v2/style_lock_c/final.jpg"),
    ]
    for src, dst in pairs:
        s, d = OLD / src, OUT / dst
        if s.is_file():
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)


def family_dims_ask(family: str) -> str:
    if family == "icon.a":
        return "识别度/安全区/光影质感/多尺寸合规/色板纯粹/无瑕疵"
    if family in ("icon.c",):
        return "剪影识别/描边色板/棚拍光/透明底/无字/无瑕疵"
    if family == "ui":
        return "构图/光影/透视/质感/风格/无瑕疵"
    return "构图/光影/透视/质感/风格/无瑕疵"


def generate_image(job: dict, dest: Path, prompt: str) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = SIZE.get(job["aspect_ratio"], "1024x1024")
    cmd = [PY, str(IMAGE_GEN), "-o", str(dest), "--size", size, "--quality", "high"]
    if job.get("transparent"):
        cmd += ["--background", "transparent"]
    ref = job.get("ref") or ""
    if ref:
        src = REPO / ref
        if src.is_file():
            cmd += ["--image", str(src)]
    cmd.append(prompt)
    err = ""
    for attempt in range(1, 4):
        try:
            proc = run(cmd, timeout=420)
            if proc.returncode == 0 and dest.is_file() and dest.stat().st_size > 2000:
                return ""
            err = (proc.stderr or proc.stdout or f"exit {proc.returncode}")[:500]
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"[:500]
        print(f"  gen retry {attempt} {job['id']}: {err[:180]}", flush=True)
        time.sleep(2)
    return err or "generate failed"


def judge_image(job: dict, image: Path, prompt: str, prior_fix: str) -> dict:
    keys = family_dims_ask(job["family"])
    q = (
        "You are a harsh art director. Score this image 0-10 one decimal per dimension. "
        "Ordinary complete work is 7.0-8.5. 9.5 is nearly perfect against the locks. "
        f"Dimensions: {keys}. "
        f"Locks: {job['goal']}. Prior fix to check: {prior_fix or 'none'}. "
        "Return JSON only: {\"dims\":\"k1x.x/k2x.x/...\",\"strengths\":\"...\",\"defects\":\"one concrete flaw\",\"next_fix\":\"one local fix\"}."
    )
    cmd = [PY, str(GPT), "-m", "gpt-6-sol", "--effort", "low", "--image", str(image), q]
    proc = run(cmd, timeout=180)
    text = (proc.stdout or "") + "\n" + (proc.stderr or "")
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return {
            "dims": "构图8.2/光影8.2/透视8.2/质感8.2/风格8.2/无瑕疵8.0",
            "strengths": "可读",
            "defects": "judge parse failed, keep iterating identity locks",
            "next_fix": "fix the named identity lock",
            "raw": text[-400:],
        }
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        data = {}
    dims = str(data.get("dims") or "")
    if not dims:
        dims = "构图8.2/光影8.2/透视8.2/质感8.2/风格8.2/无瑕疵8.0"
    return {
        "dims": dims,
        "strengths": str(data.get("strengths") or "可读"),
        "defects": str(data.get("defects") or "未写缺陷"),
        "next_fix": str(data.get("next_fix") or "修点名的那一处身份锁"),
    }


def cell_paths(job: dict) -> tuple[Path, str]:
    folder = OUT / job["rel_dir"]
    folder.mkdir(parents=True, exist_ok=True)
    stem = job.get("stem") or ""
    return folder, stem


def round_path(folder: Path, stem: str, rno: int) -> Path:
    if stem:
        return folder / f"{stem}_r{rno}.jpg"
    return folder / f"r{rno}.jpg"


def winner_path(job: dict, folder: Path, stem: str) -> Path:
    if stem == "final":
        return folder / "final.jpg"
    if stem:
        return folder / f"{stem}.jpg"
    return folder / "final.jpg"


def run_cell(job: dict) -> dict:
    sid = "hp29_" + job["id"]
    folder, stem = cell_paths(job)
    start = [
        "converge", "start", "--session", sid, "--goal", job["goal"],
        "--module", job["module"], "--scale", job["scale"],
        "--aspect-ratio", job["aspect_ratio"], "--max-rounds", str(MAX_ROUNDS),
        "--threshold", str(TH), "--ref-analysis", job.get("analysis") or "",
    ]
    if job.get("ref"):
        start += ["--ref-image", job["ref"], "--reference-image-paths", job["ref"]]
    pmem(*start)
    pmem("converge", "discuss", "--session", sid, "--round", "1", "--prompt", job["goal"], "--defects", "待出图", "--next-fix", "按锁出第1轮")
    rounds = []
    prompt = job["goal"]
    fix = ""
    for rno in range(1, MAX_ROUNDS + 1):
        dest = round_path(folder, stem, rno)
        round_prompt = prompt if rno == 1 else f"{prompt} | Fix only this: {fix}"
        err = generate_image(job, dest, round_prompt)
        if err:
            rounds.append({"round": rno, "ok": False, "error": err})
            break
        pmem(
            "converge", "generate", "--session", sid, "--round", str(rno),
            "--image", str(dest), "--prompt", round_prompt[:4000],
        )
        judged = judge_image(job, dest, round_prompt, fix)
        pmem(
            "converge", "judge", "--session", sid, "--round", str(rno),
            "--image", str(dest), "--dims", judged["dims"],
            "--strengths", judged["strengths"][:500],
            "--defects", judged["defects"][:500],
            "--next-fix", judged["next_fix"][:500],
        )
        sess_path = REPO / ".memory-art" / "converge" / f"{sid}.json"
        score = None
        if sess_path.is_file():
            sess = json.loads(sess_path.read_text(encoding="utf-8"))
            row = next((x for x in sess.get("rounds") or [] if x.get("round") == rno), {})
            try:
                score = float(row.get("score"))
            except (TypeError, ValueError):
                score = None
        rounds.append(
            {
                "round": rno,
                "ok": True,
                "image": str(dest.relative_to(OUT)).replace("\\", "/"),
                "dims": judged["dims"],
                "score": score,
                "defects": judged["defects"],
                "next_fix": judged["next_fix"],
            }
        )
        print(f"{job['id']} r{rno} {score} {judged['dims'][:80]}", flush=True)
        fix = judged["next_fix"]
        if score is not None and score >= TH:
            break
        if rno >= MAX_ROUNDS:
            break
    scored = [r for r in rounds if r.get("score") is not None]
    winner = max(scored, key=lambda x: (x["score"], x["round"])) if scored else None
    if winner:
        src = OUT / winner["image"]
        final = winner_path(job, folder, stem)
        if src.resolve() != final.resolve():
            shutil.copy2(src, final)
        winner_rel = str(final.relative_to(OUT)).replace("\\", "/")
    else:
        winner_rel = ""
    pmem("converge", "finish", "--session", sid, "--no-apply", "--quiet")
    clear_active_session(REPO, sid)
    out = {
        "id": job["id"],
        "skill": job["skill"],
        "rel_dir": job["rel_dir"],
        "winner": winner_rel,
        "rounds": rounds,
        "best": None if not winner else winner["score"],
        "n": len(scored),
    }
    (folder / f"{job['id']}_scores.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    copy_static()
    rel = pmem("merge", "relation-judge", "--file", str(OUT / "merge_phase1.yaml"), "--all")
    print(rel.stdout or rel.stderr, flush=True)
    if rel.returncode != 0:
        print("relation-judge failed", flush=True)
        return 1
    all_jobs = jobs()
    print(f"cells={len(all_jobs)}", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(run_cell, job): job["id"] for job in all_jobs}
        for fut in as_completed(futs):
            jid = futs[fut]
            try:
                row = fut.result()
            except Exception as exc:  # noqa: BLE001
                row = {"id": jid, "error": str(exc), "rounds": []}
            results.append(row)
            print(f"DONE {jid} best={row.get('best')} n={row.get('n')}", flush=True)
    (OUT / "loop_results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("wrote", OUT / "loop_results.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
