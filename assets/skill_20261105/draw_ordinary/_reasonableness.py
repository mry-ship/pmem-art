# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]

draft = (
    "Black background mushroom cheese fruit platter prop card, casual mobile game 3D style."
)

revised = (
    "Studio prop card for a top-tier casual mobile game shop: a single fly-agaric mushroom "
    "serving as a cheese-and-fruit platter, centered slightly low on a pure solid black "
    "background (#000000), three-quarter view looking slightly down, locked camera. "
    "Thick creamy-white mushroom stem supports a broad flat reddish-orange cap (#C43A1A) "
    "with large raised cream polka dots (#F5E6C8); the cap is the plate. On the left of the "
    "cap: a Swiss cheese rectangular block with a smaller triangular wedge stacked on top, "
    "pale gold (#E8C45A) with clear round eyes. Front-left and back-right: two teardrop "
    "blueberries (#2F6FB5), matte soft. Center-right: three plump orange-red cherries "
    "(#E85A2A) with short brown stems. Back-right: three bright green leaves (#3FA84A) "
    "adding height. Soft top studio key light, wide gentle highlights, short contact AO "
    "shadows where foods touch the cap; soft-round thick semi-matte casual-game 3D surface, "
    "commercial prop-card finish, silhouette readable at thumbnail. Medium polish only: "
    "keep the same layout and element list; one visible polish on cheese hole clarity and "
    "contact shadows. No text, no scene, no neon, no oily mirror plastic, no competitor "
    "pixel copy. Square 1:1."
)

checklist = (
    "subject_action=ok;contact_scale=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok"
)

cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "reasonableness",
    "review",
    "--id",
    "battery1105-ordinary",
    "--skill",
    "ordinary",
    "--draft",
    draft,
    "--revised",
    revised,
    "--checklist",
    checklist,
]
proc = subprocess.run(
    cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace"
)
Path(__file__).with_name("_reasonableness_out.txt").write_text(
    f"exit={proc.returncode}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}\n",
    encoding="utf-8",
)
Path(__file__).with_name("_revised_prompt.txt").write_text(revised, encoding="utf-8")
sys.exit(proc.returncode)
