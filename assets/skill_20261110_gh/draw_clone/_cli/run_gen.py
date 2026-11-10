import subprocess
import sys
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
cli = root / "assets/skill_20261110_gh/draw_clone/_cli"
cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "converge",
    "generate",
    "--session",
    "gh-clone-scribe-1110",
    "--conversation",
    "gh-draw-clone-20261110",
    "--route-id",
    "draw.clone",
    "--round",
    "1",
]
r = subprocess.run(cmd, cwd=root, capture_output=True)
(cli / "gen1.txt").write_bytes(r.stdout)
(cli / "gen1.err").write_bytes(r.stderr)
sys.stdout.buffer.write(r.stdout)
sys.stdout.buffer.write(r.stderr)
sys.exit(r.returncode)
