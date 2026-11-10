import subprocess
import sys
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
cli = root / "assets/skill_20261110_gh/draw_clone/_cli"
image = str(root / "assets/skill_20261110_gh/draw_clone/r3.png")
base = [sys.executable, "-u", str(root / "pmem_art.py"), "converge"]
common = [
    "--session", "gh-clone-scribe-1110",
    "--conversation", "gh-draw-clone-20261110",
    "--route-id", "draw.clone",
    "--round", "3",
    "--image", image,
]
prompt = (cli / "revised3.txt").read_text(encoding="utf-8").strip()
gen = subprocess.run(base + ["generate", "--prompt", prompt] + common, cwd=root, capture_output=True)
sys.stdout.buffer.write(b"--- GENERATE ---\n")
sys.stdout.buffer.write(gen.stdout[-2500:])
sys.stdout.buffer.write(gen.stderr)
if gen.returncode != 0:
    sys.exit(gen.returncode)
judge = subprocess.run(
    base + ["judge"] + common + [
        "--dims", "构图9.1/光影9.4/透视8.6/质感9.2/风格9.1/无瑕疵9.0",
        "--strengths", (cli / "s3.txt").read_text(encoding="utf-8").strip(),
        "--defects", (cli / "d3.txt").read_text(encoding="utf-8").strip(),
        "--next-fix", (cli / "n3.txt").read_text(encoding="utf-8").strip(),
    ],
    cwd=root, capture_output=True,
)
sys.stdout.buffer.write(b"\n--- JUDGE ---\n")
sys.stdout.buffer.write(judge.stdout)
sys.stdout.buffer.write(judge.stderr)
sys.exit(judge.returncode)
