# -*- coding: utf-8 -*-
"""Capture pmem_art CLI stdout/stderr to a file (pythonw-safe)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(sys.argv[1])
ARGS = sys.argv[2:]

exe = Path(sys.executable)
py = exe.with_name("python.exe") if exe.name.lower() == "pythonw.exe" else exe
if not py.exists():
    py = exe

cmd = [str(py), "-u", str(ROOT / "pmem_art.py"), *ARGS]
r = subprocess.run(
    cmd,
    cwd=str(ROOT),
    capture_output=True,
    text=True,
    encoding="utf-8",
    errors="replace",
)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text((r.stdout or "") + (r.stderr or ""), encoding="utf-8")
sys.exit(r.returncode)
