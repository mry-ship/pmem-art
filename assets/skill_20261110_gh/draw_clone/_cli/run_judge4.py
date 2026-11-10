import subprocess
import sys
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
cli = root / "assets/skill_20261110_gh/draw_clone/_cli"
image = str(root / "assets/skill_20261110_gh/draw_clone/r4.png")
base = [sys.executable, "-u", str(root / "pmem_art.py"), "converge"]
common = [
    "--session", "gh-clone-scribe-1110",
    "--conversation", "gh-draw-clone-20261110",
    "--route-id", "draw.clone",
    "--round", "4",
    "--image", image,
]
prompt = (cli / "revised4.txt").read_text(encoding="utf-8").strip()
gen = subprocess.run(base + ["generate", "--prompt", prompt] + common, cwd=root, capture_output=True)
sys.stdout.buffer.write(b"--- GENERATE ---\n")
sys.stdout.buffer.write(gen.stderr)
if gen.returncode != 0:
    sys.stdout.buffer.write(gen.stdout[-2000:])
    sys.exit(gen.returncode)
judge = subprocess.run(
    base + ["judge"] + common + [
        "--dims", "构图8.9/光影9.3/透视8.6/质感9.1/风格9.0/无瑕疵8.8",
        "--strengths", (cli / "s4.txt").read_text(encoding="utf-8").strip(),
        "--defects", (cli / "d4.txt").read_text(encoding="utf-8").strip(),
        "--next-fix", (cli / "n4.txt").read_text(encoding="utf-8").strip(),
    ],
    cwd=root, capture_output=True,
)
sys.stdout.buffer.write(b"\n--- JUDGE ---\n")
sys.stdout.buffer.write(judge.stdout)
sys.stdout.buffer.write(judge.stderr)
if judge.returncode != 0:
    sys.exit(judge.returncode)
fin = subprocess.run(
    base + ["finish", "--session", "gh-clone-scribe-1110", "--conversation", "gh-draw-clone-20261110"],
    cwd=root, capture_output=True,
)
sys.stdout.buffer.write(b"\n--- FINISH ---\n")
sys.stdout.buffer.write(fin.stdout)
sys.stdout.buffer.write(fin.stderr)
sys.exit(fin.returncode)
