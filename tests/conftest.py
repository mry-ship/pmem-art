"""pytest：允许测试跳闸（仍须 skip 标志）。"""
from __future__ import annotations

import os

os.environ.setdefault("PMEM_ART_ALLOW_GATE_SKIP", "1")
os.environ.setdefault("PMEM_ART_UNDER_TEST", "1")
