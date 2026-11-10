# -*- coding: utf-8 -*-
import json
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\skill_20261110\reports")
rows = []
for path in sorted(root.glob("result_*.json")):
    data = json.loads(path.read_text(encoding="utf-8"))
    images = data.get("images") or []
    gen = []
    for image in images:
        gen.append(
            {
                "part": image.get("part") or image.get("state") or "",
                "round": image.get("round"),
                "path": image.get("path"),
                "sec": image.get("duration_sec"),
                "score": image.get("score"),
                "passed": image.get("passed"),
            }
        )
    rows.append(
        {
            "file": path.name,
            "route_id": data.get("route_id"),
            "variant": data.get("variant"),
            "banner": data.get("banner"),
            "ok": data.get("ok"),
            "passed": data.get("passed_threshold"),
            "best": data.get("best_score"),
            "final": data.get("final_image"),
            "sheet": data.get("sheet_image"),
            "wall_start": data.get("wall_started_at"),
            "wall_end": data.get("wall_ended_at"),
            "wall_sec": data.get("wall_sec"),
            "notes": (data.get("notes") or "")[:240],
            "relation": data.get("relation_passed"),
            "images": gen,
        }
    )
out = root / "_digest.json"
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(len(rows))
