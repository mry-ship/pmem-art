# -*- coding: utf-8 -*-
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
OUT = ROOT / "assets" / "skill_20261112_suite" / "out" / "ui.kit"
PY = sys.executable
CONV = "suite_ui_kit"
OUT.mkdir(parents=True, exist_ok=True)


def run(name: str, args: list[str]) -> int:
    out_path = OUT / f"{name}.out.txt"
    err_path = OUT / f"{name}.err.txt"
    cmd = [PY, "-u", str(ROOT / "pmem_art.py"), *args]
    print(f"=== {name} ===", flush=True)
    with out_path.open("w", encoding="utf-8") as fo, err_path.open("w", encoding="utf-8") as fe:
        p = subprocess.run(cmd, cwd=str(ROOT), stdout=fo, stderr=fe, text=True, encoding="utf-8")
    out_text = out_path.read_text(encoding="utf-8", errors="replace")
    err_text = err_path.read_text(encoding="utf-8", errors="replace")
    if out_text:
        print(out_text, flush=True)
    if err_text:
        print("ERR:", err_text, flush=True)
    print(f"EXIT={p.returncode}", flush=True)
    return p.returncode


def main() -> int:
    goal = (
        "/pmem-ui Brimwave Cafe casual merge main-menu HUD concept, "
        "warm harbor cafe, soft glossy casual UI; 用这份稿 as style/layout pads only"
    )
    refs = "assets/skill_20261112_suite/refs/ref_ui.png,assets/skill_20261112_suite/refs/ref_ui_dl.jpg"
    ref_analysis = (
        "Pad images are casual-merge renovation HUD: soft glossy rounded chrome top resource pills, "
        "thick readable numerals, scene fills screen, controls overlay isometric interior. "
        "Lock chrome craft and soft-gloss casual UI vibe. Do NOT pixel-copy Design three-choice "
        "bar, kitchen layout, or character portraits."
    )

    # Keep route text == goal so route-gate goal match passes under concurrency.
    code = run(
        "00_route",
        [
            "route",
            "--text",
            goal,
            "--canonical",
            "整套界面或 HUD 或九宫格与状态族；走界面",
            "--conversation",
            CONV,
        ],
    )
    if code != 0:
        return code

    code = run(
        "01_start",
        [
            "converge",
            "start",
            "--session",
            "suite_ui_kit",
            "--module",
            "ui.BrimwaveCafe",
            "--route-id",
            "ui.kit",
            "--scale",
            "high",
            "--goal",
            goal,
            "--reference-image-paths",
            refs,
            "--aspect-ratio",
            "9:16",
            "--ref-analysis",
            ref_analysis,
            "--conversation",
            CONV,
        ],
    )
    if code != 0:
        return code

    code = run(
        "02_contract",
        [
            "contract",
            "set",
            "--id",
            "suite_ui_kit",
            "--defaults",
            "default: concept-only; 9:16 portrait; main-menu concept only; no component sheet/9-slice/state family; Cursor GenerateImage; full-bleed scene",
            "--locks",
            "subject=Brimwave Cafe harbor casual-merge cafe main menu; style=pad soft-gloss casual HUD chrome; top single-row resources; lower-mid largest PLAY CTA; full-bleed scene; chrome over scene; warm harbor cafe mood; readable Brimwave Cafe + PLAY; no gibberish",
            "--unlocks",
            "no pixel-copy pad kitchen / Design 3-choice bar / character portraits; unlock RM five-tab default; unlock component sheets",
            "--vibe",
            "benchmark category=casual merge main-menu HUD (ui.casual_hud): store-screenshot density, clear top resources, largest primary CTA, chrome same soft-gloss family as harbor cafe scene",
        ],
    )
    if code != 0:
        return code

    discuss = (
        "concept-only main menu 9:16. Warm harbor cafe scene fills screen (afternoon harbor light, "
        "pastry counter, coffee steam). NOT a Design renovation picker. Top single-row: level + energy "
        "+ coins + gems, soft rounded white chrome thick borders. Lower-mid largest PLAY CTA. Tiny "
        "settings gear corner. Optional light Home-centered bottom nav (not PvP lobby). Face clear of "
        "chrome. No gibberish, no fake phone bezel."
    )
    code = run(
        "03_discuss",
        ["converge", "discuss", "--id", "suite_ui_kit", "--text", discuss],
    )
    if code != 0:
        return code

    draft = "Brimwave Cafe main menu HUD soft glossy casual UI 9:16"
    revised = (
        "Mobile 9:16 casual-merge MAIN MENU HUD concept for Brimwave Cafe "
        "(NOT a Design renovation picker screen). Full-bleed warm harbor cafe interior scene under "
        "soft afternoon window light: creamy wood counters, teal accents, pastry trays, coffee steam, "
        "distant harbor boats through big windows. Soft glossy toy-plastic casual UI chrome matching "
        "pad craft (rounded white resource pills, thick blue/cream borders, chunky readable numerals "
        "with dark outlines) — do not copy pad pixel layout. "
        "TOP single-row HUD: level circle + energy + coins + gems; tiny settings gear top-right corner, "
        "not a second row. MID scene: friendly cafe barista as emotional anchor with face clear of chrome; "
        "leave lower floor clear for CTA. LOWER-MID primary CTA: one oversized soft-gloss PLAY button "
        "(or Level xx), clearly largest interactive element. OPTIONAL light bottom nav with Home centered "
        "(casual merge, not PvP lobby, not Royal Match five-tab default if it fights cafe identity). "
        "Readable logo text Brimwave Cafe near top or above CTA. No gibberish, no phone bezel, "
        "no Design three-option strip, no match-3 board. "
        "Benchmark category = casual merge main-menu HUD (ui.casual_hud): store-screenshot density, "
        "chrome same family as scene, soft glossy warm saturated finish."
    )
    checklist = (
        "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;"
        "layout_zones=ok;no_content_clutter=ok;chrome_not_illustration=ok;"
        "cta_clear_of_faces=ok;control_craft=ok"
    )
    code = run(
        "04_reason",
        [
            "reasonableness",
            "review",
            "--id",
            "suite_ui_kit",
            "--skill",
            "ui",
            "--draft",
            draft,
            "--revised",
            revised,
            "--checklist",
            checklist,
            "--notes",
            "concept-only; benchmark=casual merge main-menu HUD; pads lock chrome craft only, no pixel copy",
        ],
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
