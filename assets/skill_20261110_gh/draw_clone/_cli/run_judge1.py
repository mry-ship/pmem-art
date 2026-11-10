import subprocess
import sys
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
cli = root / "assets/skill_20261110_gh/draw_clone/_cli"
image = str(root / "assets/skill_20261110_gh/draw_clone/r1.png")
base = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "converge",
]
common = [
    "--session",
    "gh-clone-scribe-1110",
    "--conversation",
    "gh-draw-clone-20261110",
    "--route-id",
    "draw.clone",
    "--round",
    "1",
    "--image",
    image,
]
gen = subprocess.run(base + ["generate"] + common, cwd=root, capture_output=True)
(cli / "gen1b.txt").write_bytes(gen.stdout)
(cli / "gen1b.err").write_bytes(gen.stderr)
sys.stdout.buffer.write(b"--- GENERATE ---\n")
sys.stdout.buffer.write(gen.stdout)
sys.stdout.buffer.write(gen.stderr)
if gen.returncode != 0:
    sys.exit(gen.returncode)

strengths = (cli / "s1.txt").read_text(encoding="utf-8").strip()
defects = (cli / "d1.txt").read_text(encoding="utf-8").strip()
nxt = (cli / "n1.txt").read_text(encoding="utf-8").strip()
judge = subprocess.run(
    base
    + ["judge"]
    + common
    + [
        "--dims",
        "构图9.2/光影9.4/透视8.6/质感9.2/风格8.9/无瑕疵9.1",
        "--strengths",
        strengths,
        "--defects",
        defects,
        "--next-fix",
        nxt,
    ],
    cwd=root,
    capture_output=True,
)
(cli / "judge1.txt").write_bytes(judge.stdout)
(cli / "judge1.err").write_bytes(judge.stderr)
sys.stdout.buffer.write(b"\n--- JUDGE ---\n")
sys.stdout.buffer.write(judge.stdout)
sys.stdout.buffer.write(judge.stderr)
sys.exit(judge.returncode)
