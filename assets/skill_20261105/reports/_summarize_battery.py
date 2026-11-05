from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
conv = root / ".memory-art" / "converge"
out = root / "assets" / "skill_20261105"
reports = out / "reports"

print("=== converge sessions ===")
for p in sorted(conv.glob("battery1105*.json")):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(p.stem, "READ_FAIL", e)
        continue
    rounds = d.get("rounds") or []
    best = None
    for r in rounds:
        sc = r.get("score")
        if sc is None:
            continue
        if best is None or float(sc) > float(best[0]):
            best = (float(sc), r.get("round"), r.get("image"))
    print(
        f"{p.stem}: status={d.get('status') or d.get('state')} "
        f"rounds={len(rounds)} best={best} module={d.get('module')} "
        f"finished={d.get('finished')}"
    )

print("\n=== result json ===")
for p in sorted(reports.glob("result_*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    print(
        p.name,
        "score=",
        d.get("score"),
        "passed=",
        d.get("passed_threshold"),
        "status=",
        d.get("status"),
        "out=",
        d.get("output_image") or d.get("final_path") or d.get("outputs"),
    )

print("\n=== image presence ===")
checks = [
    "draw_ordinary/r1.png",
    "draw_ordinary/final.png",
    "draw_keyart/r1.png",
    "draw_keyart/r2.png",
    "draw_keyart/final.png",
    "draw_clone/r1.png",
    "draw_clone/final.png",
    "draw_variant/r1.png",
    "draw_variant/final.png",
    "draw_multi/r1.png",
    "draw_multi/final.png",
    "ui_concept/final.png",
    "icon_a/final.png",
    "icon_c/prop_mushroom_platter.png",
    "icon_c/final.png",
    "merge_overview/final.jpg",
    "merge_overview/merge_overview_r1.jpg",
]
for rel in checks:
    p = out / rel
    print(("OK" if p.is_file() else "NO"), rel, p.stat().st_size if p.is_file() else "")
