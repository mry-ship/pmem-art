#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

from rerun_homepage_5scale import LABEL, compose_prompt, select_bots  # noqa: E402

OUT = REPO / "docs" / "showcase" / "rerun_5scale_opt1027"
OUT.mkdir(parents=True, exist_ok=True)
(OUT / "images").mkdir(parents=True, exist_ok=True)

best = json.loads((REPO / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
bots = select_bots()
jobs = []
for b in bots:
    prompt = compose_prompt(b, best)
    short = LABEL[b["display_scale"]]
    jobs.append(
        {
            "bot_id": b["bot_id"],
            "slug": b["slug"],
            "scale": b["display_scale"],
            "short": short,
            "aspect": b.get("aspect_ratio") or "1:1",
            "ref": str(REPO / b["ref_image"]),
            "prompt": prompt,
            "out_name": f"{b['slug']}_{short}.png",
            "out": str(OUT / "images" / f"{b['slug']}_{short}.png"),
        }
    )

(OUT / "jobs.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {len(jobs)} jobs -> {OUT / 'jobs.json'}")
for j in jobs:
    print(f"{j['bot_id']} {j['slug']} {j['short']} {j['aspect']} len={len(j['prompt'])}")
