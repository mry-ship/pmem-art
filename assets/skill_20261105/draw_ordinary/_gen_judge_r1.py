# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[3]
session = "battery1105-ordinary"
image = "assets/skill_20261105/draw_ordinary/r1.png"
revised = Path(__file__).with_name("_revised_prompt.txt").read_text(encoding="utf-8").strip()


def run(args: list[str]) -> subprocess.CompletedProcess:
    cmd = [sys.executable, "-u", str(root / "pmem_art.py"), *args]
    return subprocess.run(
        cmd, cwd=str(root), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


g = run(
    [
        "converge",
        "generate",
        "--session",
        session,
        "--round",
        "1",
        "--image",
        image,
        # omit --prompt so first round uses revised
    ]
)
Path(__file__).with_name("_generate_r1.txt").write_text(
    f"exit={g.returncode}\nSTDOUT:\n{g.stdout}\nSTDERR:\n{g.stderr}\n",
    encoding="utf-8",
)
if g.returncode != 0:
    sys.exit(g.returncode)

# Placeholder dims — real judge script will be updated after visual review
# This file only does generate; judge is separate after Read.
sys.exit(0)
