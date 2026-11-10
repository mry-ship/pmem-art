# -*- coding: utf-8 -*-
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
sys.path.insert(0, str(ROOT))
from skills_kit.skill_registry import build_registry, slice_route_body
from skills_kit.skill_specs import SKILL_SPECS

out = ROOT / "assets" / "skill_20261110" / "reports"
out.mkdir(parents=True, exist_ok=True)
reg = build_registry(SKILL_SPECS, installed_root=ROOT)
by_name = {s["name"]: s["body"] for s in SKILL_SPECS}
rows = []
for route in reg["routes"]:
    packed = slice_route_body(by_name[route["skill"]], route)
    name = route["id"].replace(".", "_")
    path = out / f"pack_{name}.md"
    path.write_text(packed, encoding="utf-8")
    rows.append(f"{route['id']}\t{route['skill']}\t{len(packed)}\t{path.name}")
(out / "manifest.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
print("\n".join(rows))
