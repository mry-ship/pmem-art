"""Session reflections I/O."""
from __future__ import annotations

import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

from .project_library import (
    ensure_project_library_bound,
    slugify_project_id,
    sync_active_project_to_library,
)
from .taste_profile import reflections_dir

# ---------------------------------------------------------------------------
# Session reflection (after converge finish; memory apply is default)
# ---------------------------------------------------------------------------

def write_session_reflection(
    root: Path,
    sess: dict[str, Any],
    *,
    winner: dict[str, Any] | None = None,
    outcome: str = "",
) -> Path:
    winner = winner or sess.get("winner") or {}
    rounds = sess.get("rounds") or []
    stamp = _now_cst().strftime("%Y%m%d_%H%M%S")
    sid = sess.get("session_id") or "latest"
    path = reflections_dir(root) / f"{stamp}_{sid}.json"

    passed = [r for r in rounds if r.get("passed")]
    failed = [r for r in rounds if not r.get("passed")]
    fixed = [r.get("next_fix") for r in failed if r.get("next_fix")]
    still_weak = winner.get("defects") if winner and not winner.get("passed") else ""
    if winner and winner.get("passed"):
        still_weak = "无明显硬伤（已达标）" if not (winner.get("defects") or "").strip() else f"残余可接受点：{winner.get('defects')}"

    taste_deltas: dict[str, list[str]] = {
        "from_strengths": [],
        "from_defects": [],
    }
    if winner.get("strengths"):
        taste_deltas["from_strengths"].append(str(winner["strengths"])[:120])
    for r in failed[-3:]:
        if r.get("defects"):
            taste_deltas["from_defects"].append(str(r["defects"])[:100])

    meta = ensure_project_library_bound(root)
    reflection = {
        "schema": "pmem-art.reflection.v1",
        "project_id": meta.get("project_id") or slugify_project_id(root.name),
        "project_name": meta.get("project_name") or root.name,
        "layer_scope": "private",
        "written_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
        "session_id": sid,
        "goal": sess.get("goal"),
        "module": sess.get("module"),
        "converge_mode": sess.get("converge_mode") or sess.get("quality_mode") or "quality",
        "guided_mode": sess.get("mode"),
        "threshold": sess.get("accept_threshold", sess.get("threshold", 9.6)),
        "max_rounds": sess.get("max_rounds", 8),
        "rounds_used": len(rounds),
        "winner_round": winner.get("round"),
        "winner_score": winner.get("score"),
        "winner_image": winner.get("image"),
        "winner_passed": bool(winner.get("passed")),
        "outcome": outcome,
        "what_fixed": fixed[-6:],
        "what_still_weak": still_weak,
        "strengths": winner.get("strengths"),
        "taste_deltas": taste_deltas,
        "warm_start_confidence": (sess.get("warm_start") or {}).get("confidence"),
        "fast_track": bool(sess.get("fast_track")),
        "scores": [{"round": r.get("round"), "score": r.get("score"), "passed": r.get("passed")} for r in rounds],
    }
    path.write_text(json.dumps(reflection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sync_active_project_to_library(root)
    return path


def list_reflections(root: Path, limit: int = 30) -> list[dict[str, Any]]:
    d = reflections_dir(root)
    files = sorted(d.glob("*.json"), key=lambda p: p.name, reverse=True)[:limit]
    out: list[dict[str, Any]] = []
    for f in files:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


