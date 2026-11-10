import subprocess
import sys
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
cli = root / "assets/skill_20261110_gh/draw_clone/_cli"
draft = (cli / "draft.txt").read_text(encoding="utf-8").strip()
revised = (cli / "revised.txt").read_text(encoding="utf-8").strip()
cmd = [
    sys.executable,
    "-u",
    str(root / "pmem_art.py"),
    "reasonableness",
    "review",
    "--id",
    "gh-clone-scribe-1110",
    "--skill",
    "clone",
    "--draft",
    draft,
    "--revised",
    revised,
    "--checklist",
    "subject_action=ok;contact_scale=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;new_subject_not_ref_echo=ok",
]
r = subprocess.run(cmd, cwd=root, capture_output=True)
(cli / "review.txt").write_bytes(r.stdout)
(cli / "review.err").write_bytes(r.stderr)
sys.stdout.buffer.write(r.stdout)
sys.stdout.buffer.write(r.stderr)
sys.exit(r.returncode)
