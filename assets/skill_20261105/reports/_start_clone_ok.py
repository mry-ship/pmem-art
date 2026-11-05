from __future__ import annotations

import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(root))
from skills_kit.route_gate import seed_named_route

cid = sid = "battery1105-clone-ok"
goal = "克隆：锁妖精花园粘土童话画风，换新题材冬日农场雪地农夫抱小羊。禁止抄参考构图分区与物件。"
ref = "assets/skill_20261103/01_style.png"
assert (root / ref).is_file(), f"missing {ref}"
seed_named_route(root, "draw.clone", goal=goal, conversation_id=cid)
cmd = [
    "pyw", "-3", "-u", "pmem_art.py", "converge", "start",
    "--session", sid, "--route-id", "draw.clone", "--conversation", cid,
    "--goal", goal, "--module", "scene.WinterFarm.FairyClay",
    "--ref-image", ref, "--ref-analysis", "风格锁粘土童话；不锁构图",
    "--medium-family", "立体", "--mode", "quality",
]
r = subprocess.run(cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace")
log = Path(__file__).with_name("_clone_ok_start.txt")
log.write_text((r.stdout or "") + "\n" + (r.stderr or "") + f"\nEXIT {r.returncode}\n", encoding="utf-8")
print(log.read_text(encoding="utf-8")[-1800:])
raise SystemExit(r.returncode)
