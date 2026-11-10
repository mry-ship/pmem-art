# -*- coding: utf-8 -*-
"""Run pmem_art.main and capture stdout, because pyw often drops the console."""
import sys
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art")
sys.path.insert(0, str(ROOT))
if len(sys.argv) < 3:
    raise SystemExit("usage: _cli.py <outfile> <pmem_art args...>")
out = Path(sys.argv[1])
out.parent.mkdir(parents=True, exist_ok=True)
sys.argv = ["pmem_art.py", *sys.argv[2:]]
with out.open("w", encoding="utf-8") as handle:
    sys.stdout = handle
    sys.stderr = handle
    import pmem_art

    code = pmem_art.main()
raise SystemExit(code)
