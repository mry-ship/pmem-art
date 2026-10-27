"""Backward-compatible re-export — canonical module is skills_kit.converge_policy. """
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from skills_kit.converge_policy import *  # noqa: F403
from skills_kit.converge_policy import (  # noqa: F401
    DEFAULT_ANATOMY_FLOOR,
    DEFAULT_AUTO_PAD_DROP,
    DEFAULT_EARLY_STOP_MIN_ROUND,
    DEFAULT_PAD_MODE,
    DEFAULT_PLATEAU_ROUNDS,
    DEFAULT_REGRESSION_DROP,
    PROMPT_CHAR_BUDGET,
    anatomy_ok_for_stop,
    anatomy_score,
    anatomy_score_loose,
    choose_next_pad,
    coerce_dims_dict,
    decide_round_stop,
    dim_float,
    pick_best_round_on_stop,
    plate_safe_to_pad,
    rewrite_reflow_by_dims,
    should_force_ref_pad,
    truncate_prompt,
)
