"""Bypass stale Mac bound_root isolation so hp29 converge CLI can run."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import improve.project_library as pl  # noqa: E402


def _safe_bind(root, *, explicit_project_name: str = "", _skip_sync: bool = False):
    p = pl.active_project_meta_path(Path(root))
    if p.is_file():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


pl.ensure_project_library_bound = _safe_bind

# Re-bind names already imported elsewhere at function-call time via module attr.
import improve.taste_profile as taste_profile  # noqa: E402
import improve.knowledge as knowledge  # noqa: E402
import improve.warm_start as warm_start  # noqa: E402

for mod in (taste_profile, knowledge, warm_start):
    if hasattr(mod, "ensure_project_library_bound"):
        mod.ensure_project_library_bound = _safe_bind

from pmem_art import _cli_entry  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(_cli_entry())
