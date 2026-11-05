from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
reports = root / "assets" / "skill_suite_20261105" / "reports"


def load_json(p: Path) -> dict:
    raw = p.read_text(encoding="utf-8-sig").strip()
    if not raw.startswith("{"):
        i = raw.find("{")
        raw = raw[i:] if i >= 0 else raw
    return json.loads(raw)


print("=== SESSIONS ===")
rows = []
for p in sorted((root / ".memory-art" / "converge").glob("battery1105*.json")):
    d = json.loads(p.read_text(encoding="utf-8"))
    rounds = d.get("rounds") or []
    best = None
    for r in rounds:
        sc = r.get("score")
        if sc is None:
            continue
        if best is None or float(sc) > float(best[0]):
            best = (float(sc), r.get("round"), r.get("image"))
    print(f"{p.stem}: status={d.get('status')} rounds={len(rounds)} best={best}")

print("\n=== RESULTS ===")
for p in sorted(reports.glob("result_*.json")):
    try:
        d = load_json(p)
    except Exception as e:
        print(p.name, "PARSE_FAIL", e)
        continue
    score = d.get("score") or d.get("best_score") or d.get("winner_score")
    passed = d.get("passed")
    if passed is None:
        passed = d.get("passed_threshold")
    if passed is None:
        passed = d.get("passed_threshold_9_5")
    print(
        f"{p.name}: score={score} passed={passed} status={d.get('status')} "
        f"rounds={d.get('rounds') or d.get('rounds_used')}"
    )
    if d.get("defects"):
        print("  defects:", str(d["defects"])[:200])
    if d.get("notes"):
        print("  notes:", str(d["notes"])[:200])

# presence of closing skills
print("\n=== CLOSING ===")
for name in ("result_critique_review.json", "result_atlas_file.json", "result_coach_report.json", "result_draw_clone.json", "result_draw_variant.json"):
    print(name, "OK" if (reports / name).is_file() else "MISSING")
