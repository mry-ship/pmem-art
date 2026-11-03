# -*- coding: utf-8 -*-
"""Unified local pipeline for /pmem-layer-split.

Contract (prompt rules, acceptance narrative) lives in skills/*/pmem-layer-split/SKILL.md.
This package only implements calibrate / isolate / compose / gate / qa / emit.
Gate numbers here MUST stay in sync with that SKILL (see defaults.GATE).
"""

__version__ = "1.0.0"

from .defaults import GATE, SIZE_BUCKETS, QUALITY_BY_AREA

__all__ = ["GATE", "SIZE_BUCKETS", "QUALITY_BY_AREA", "__version__"]
