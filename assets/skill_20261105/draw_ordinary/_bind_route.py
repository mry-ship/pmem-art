# -*- coding: utf-8 -*-
"""Re-bind route to battery1105-ordinary conversation (parallel-safe)."""
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
goal = (
    "黑底棚拍休闲手游道具卡：毒蝇伞形蘑菇芝士果盘；蘑菇盖作盘面，上置瑞士芝士块与三角楔、"
    "泪滴蓝莓、橙红樱桃与绿叶；纯黑实色底；顶级休闲手游道具卡棚拍完成度；题材与参考不变，"
    "medium 锁机位；垫图4，走普通图"
)
cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "route",
    "--text",
    goal,
    "--canonical",
    "要画一张图；有参考；题材不变；走普通图",
    "--conversation",
    "battery1105-ordinary",
    "--json",
]
proc = subprocess.run(
    cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace"
)
Path(__file__).with_name("_bind_route.txt").write_text(
    f"exit={proc.returncode}\n{proc.stdout}\n{proc.stderr}", encoding="utf-8"
)
sys.exit(proc.returncode)
