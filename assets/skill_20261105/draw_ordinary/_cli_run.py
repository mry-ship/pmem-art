# -*- coding: utf-8 -*-
"""Run pmem_art.py with UTF-8 argv from a JSON file; write stdout/stderr to out path."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
out = Path(spec["out"])
args = list(spec["args"])

exe = Path(sys.executable)
py = exe.with_name("python.exe") if exe.name.lower() == "pythonw.exe" else exe
if not py.exists():
    py = exe

cmd = [str(py), "-u", str(ROOT / "pmem_art.py"), *args]
r = subprocess.run(
    cmd,
    cwd=str(ROOT),
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
out.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "returncode": r.returncode,
    "cmd": cmd,
    "stdout": r.stdout or "",
    "stderr": r.stderr or "",
}
out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
# also write plain for quick view
out.with_suffix(out.suffix + ".txt").write_text(
    (r.stdout or "") + (r.stderr or ""), encoding="utf-8"
)
sys.exit(0 if out.exists() else 1)
