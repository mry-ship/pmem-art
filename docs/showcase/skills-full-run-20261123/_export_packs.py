from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from skills_kit.skill_registry import build_registry, slice_route_body
from skills_kit.skill_specs import SKILL_SPECS

out = Path(__file__).resolve().parent / "packs"
out.mkdir(parents=True, exist_ok=True)
reg = build_registry(SKILL_SPECS, installed_root=ROOT)
routes = {r["id"]: r for r in reg.get("routes", [])}
ids = [
    "ui.kit",
    "icon.a",
    "icon.b",
    "icon.c",
    "merge.ladder",
    "layer.split",
    "draw.lens",
    "draw.touchup",
    "draw.clone",
    "draw.variant",
    "draw.multi",
    "draw.key",
    "style.lock",
    "critique.review",
    "atlas.file",
    "coach.report",
    "prompt.write",
    "draw.ordinary",
]
meta = []
for rid in ids:
    r = routes[rid]
    body = (ROOT / r["file"]).read_text(encoding="utf-8")
    pack = slice_route_body(body, r)
    p = out / f"{rid.replace('.', '_')}.md"
    p.write_text(pack, encoding="utf-8")
    meta.append(
        {
            "id": rid,
            "skill": r.get("skill"),
            "heading": r.get("heading"),
            "pack_headings": r.get("pack_headings"),
            "file": r.get("file"),
            "pack_path": str(p.relative_to(ROOT)).replace("\\", "/"),
            "pack_chars": len(pack),
        }
    )
(out / "_index.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
print("ok", len(meta))
for m in meta:
    print(m["id"], m["pack_chars"], m["pack_path"])
