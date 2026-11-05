from __future__ import annotations

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))

from skills_kit.route_gate import check_route_gate, seed_named_route
cid = "battery1105-clone-fix"
sid = "battery1105-clone-fix"
goal = "克隆：锁妖精花园粘土童话画风，换新题材冬日农场雪地农夫抱小羊。禁止抄参考构图分区与物件。"
seed_named_route(root, "draw.clone", goal=goal, conversation_id=cid)
print("gate", check_route_gate(root, goal=goal, expect_route="draw.clone", conversation_id=cid))
cmd = [
    "pyw",
    "-3",
    "-u",
    "pmem_art.py",
    "converge",
    "start",
    "--session",
    sid,
    "--route-id",
    "draw.clone",
    "--conversation",
    cid,
    "--goal",
    goal,
    "--module",
    "scene.WinterFarm.FairyClay",
    "--ref-image",
    "assets/skill_20261103/01_style.png",
    "--ref-analysis",
    "风格锁粘土童话；不锁构图",
    "--medium-family",
    "立体",
    "--mode",
    "quality",
]
r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
out = (r.stdout or "") + (r.stderr or "")
print(out[-2000:])
print("exit", r.returncode)
