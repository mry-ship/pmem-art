from pathlib import Path

from skills_kit.skill_registry import build_registry, slice_route_body
from skills_kit.skill_specs import SKILL_SPECS

reg = build_registry(SKILL_SPECS)
by_body = {s["name"]: s["body"] for s in SKILL_SPECS}
by_id = {r["id"]: r for r in reg["routes"]}
ids = [
    "draw.ordinary",
    "draw.key",
    "draw.clone",
    "draw.variant",
    "draw.multi",
    "draw.lens",
    "ui.kit",
    "icon.a",
    "icon.b",
    "icon.c",
    "merge.ladder",
    "style.lock",
    "prompt.write",
    "critique.review",
    "atlas.file",
    "coach.report",
]
out = Path("assets/skill_20261105/reports")
out.mkdir(parents=True, exist_ok=True)
for rid in ids:
    r = by_id[rid]
    pack = slice_route_body(by_body[r["skill"]], r)
    p = out / f"pack_{rid.replace('.', '_')}.md"
    p.write_text(
        f"# EXEC PACK {rid}\n\nbanner heading: {r.get('heading')}\nskill: {r['skill']}\n\n" + pack,
        encoding="utf-8",
    )
    print(rid, "chars", len(pack), "->", p.name)
