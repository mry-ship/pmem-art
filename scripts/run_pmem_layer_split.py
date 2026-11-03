# -*- coding: utf-8 -*-
"""Launcher: python scripts/run_pmem_layer_split.py --job assets/<job> <cmd>"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pmem_layer_split.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
