"""Record hp29 generate/judge without shell quoting issues."""
from __future__ import annotations

import argparse
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
import improve.taste_profile as taste_profile  # noqa: E402
import improve.knowledge as knowledge  # noqa: E402
import improve.warm_start as warm_start  # noqa: E402
import improve.reflection as reflection  # noqa: E402
import improve as improve_pkg  # noqa: E402

for mod in (taste_profile, knowledge, warm_start, reflection, improve_pkg):
    if hasattr(mod, "ensure_project_library_bound"):
        mod.ensure_project_library_bound = _safe_bind

from skills_kit.converge import cmd_converge  # noqa: E402
from pmem_art import load_project  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["start", "generate", "judge", "finish"])
    ap.add_argument("--session")
    ap.add_argument("--round", type=int, default=0)
    ap.add_argument("--image", default="")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--dims", default="")
    ap.add_argument("--strengths", default="")
    ap.add_argument("--defects", default="")
    ap.add_argument("--next-fix", default="")
    ap.add_argument("--goal", default="")
    ap.add_argument("--module", default="")
    ap.add_argument("--scale", default="medium")
    ap.add_argument("--aspect-ratio", default="")
    ap.add_argument("--medium-family", default="")
    ap.add_argument("--ref-image", default="")
    ap.add_argument("--ref-analysis", default="")
    args = ap.parse_args()
    data = load_project(ROOT)
    return cmd_converge(
        ROOT,
        data,
        args.action,
        session_id=args.session,
        goal=args.goal,
        module=args.module,
        ref_image=args.ref_image,
        ref_analysis=args.ref_analysis,
        threshold=9.6,
        max_rounds=4,
        round_num=args.round,
        image=args.image,
        dims=args.dims,
        strengths=args.strengths,
        defects=args.defects,
        next_fix=args.next_fix,
        prompt=args.prompt,
        apply_memory=False,
        scale=args.scale,
        aspect_ratio=args.aspect_ratio,
        reference_image_paths=args.ref_image or None,
        silent=args.action == "finish",
        medium_family=args.medium_family,
    )


if __name__ == "__main__":
    raise SystemExit(main())
