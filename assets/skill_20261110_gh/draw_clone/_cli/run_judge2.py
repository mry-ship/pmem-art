import subprocess
import sys
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
cli = root / "assets/skill_20261110_gh/draw_clone/_cli"
image = str(root / "assets/skill_20261110_gh/draw_clone/r2.png")
base = [sys.executable, "-u", str(root / "pmem_art.py"), "converge"]
common = [
    "--session", "gh-clone-scribe-1110",
    "--conversation", "gh-draw-clone-20261110",
    "--route-id", "draw.clone",
    "--round", "2",
    "--image", image,
]
prompt = (cli / "revised2.txt").read_text(encoding="utf-8").strip()
gen = subprocess.run(base + ["generate", "--prompt", prompt] + common, cwd=root, capture_output=True)
(cli / "gen2.txt").write_bytes(gen.stdout)
(cli / "gen2.err").write_bytes(gen.stderr)
sys.stdout.buffer.write(b"--- GENERATE ---\n")
sys.stdout.buffer.write(gen.stdout)
sys.stdout.buffer.write(gen.stderr)
if gen.returncode != 0:
    sys.exit(gen.returncode)
strengths = (cli / "s2.txt").read_text(encoding="utf-8").strip()
defects = (cli / "d2.txt").read_text(encoding="utf-8").strip()
nxt = (cli / "n2.txt").read_text(encoding="utf-8").strip()
judge = subprocess.run(
    base + ["judge"] + common + [
        "--dims", "构图9.2/光影9.4/透视8.5/质感9.2/风格9.1/无瑕疵9.0",
        "--strengths", strengths,
        "--defects", defects,
        "--next-fix", nxt,
    ],
    cwd=root, capture_output=True,
)
(cli / "judge2.txt").write_bytes(judge.stdout)
(cli / "judge2.err").write_bytes(judge.stderr)
sys.stdout.buffer.write(b"\n--- JUDGE ---\n")
sys.stdout.buffer.write(judge.stdout)
sys.stdout.buffer.write(judge.stderr)
sys.exit(judge.returncode)
