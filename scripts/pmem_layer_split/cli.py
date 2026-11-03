# -*- coding: utf-8 -*-
"""CLI for /pmem-layer-split local pipeline."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .job import Job
from .calibrate import setup_and_calibrate
from .bg_local import build_local_background
from .isolate import isolate_layers
from .compose import compose
from .gate import run_gate
from .qa import ghost_qa
from .emit_html import emit_html
from .defaults import DEFAULT_WORKERS, GATE


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pmem_layer_split",
        description="Local pipeline for /pmem-layer-split (calibrate→isolate→compose→gate→qa→emit)",
    )
    p.add_argument(
        "--job",
        required=True,
        help="Job directory containing split_plan.json + ref image",
    )
    p.add_argument(
        "command",
        choices=[
            "setup",
            "calibrate",
            "bg",
            "isolate",
            "compose",
            "gate",
            "qa",
            "emit",
            "status",
            "retry-dirty",
            "run-local",
            "pipeline",
        ],
        help="Subcommand",
    )
    p.add_argument("--ids", default="", help="Comma-separated layer ids (isolate/gate force)")
    p.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    p.add_argument("--force", action="store_true", help="Re-isolate even if status=ok")
    p.add_argument("--scale", type=int, default=2, help="Compose canvas scale vs ref")
    p.add_argument("--skip-match", action="store_true", help="Skip template match (trust plan crops)")
    p.add_argument("--dry-run", action="store_true", help="isolate: print targets only")
    p.add_argument("--title", default="", help="stack.html title")
    p.add_argument(
        "--bg-local",
        action="store_true",
        help="use local dig-hole bg (often muddy); default is image2.5 bg isolate",
    )
    p.add_argument(
        "--no-bg-local",
        action="store_true",
        help="deprecated alias: same as default (API bg). Kept for old commands.",
    )
    p.add_argument("--max-rounds", type=int, default=GATE["max_retries"], help="pipeline dirty retry rounds")
    return p


def _use_local_bg(args: argparse.Namespace) -> bool:
    """Default False = image2.5 bg. --bg-local opts into dig-hole."""
    if getattr(args, "bg_local", False):
        return True
    # old flag meant "don't use local / force API" — treat as API
    return False


def _ids(s: str) -> list[str] | None:
    s = (s or "").strip()
    if not s:
        return None
    return [x.strip() for x in s.split(",") if x.strip()]


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    job = Job(Path(args.job))
    ids = _ids(args.ids)

    if args.command in ("setup", "calibrate"):
        setup_and_calibrate(job, skip_match=args.skip_match)
        return 0

    if args.command == "bg":
        build_local_background(job)
        return 0

    if args.command == "isolate":
        isolate_layers(
            job,
            ids=ids,
            workers=args.workers,
            force=args.force,
            skip_bg=_use_local_bg(args),
            dry_run=args.dry_run,
        )
        return 0

    if args.command == "compose":
        compose(job, scale=args.scale)
        return 0

    if args.command == "gate":
        run_gate(job, force_ids=ids)
        return 0

    if args.command == "qa":
        ghost_qa(job, scale=args.scale)
        return 0

    if args.command == "emit":
        emit_html(job, title=args.title or None)
        return 0

    if args.command == "status":
        st = job.load_status()
        layers = st.get("layers") or {}
        for lid, info in layers.items():
            print(f"{lid}: {info.get('status')} retries={info.get('retries')} {info.get('reasons') or ''}")
        print("dirty_ids:", st.get("dirty_ids"))
        return 0

    if args.command == "retry-dirty":
        st = job.load_status()
        dirty = st.get("dirty_ids") or [
            k for k, v in (st.get("layers") or {}).items() if v.get("status") == "dirty"
        ]
        if not dirty:
            print("no dirty layers")
            return 0
        print("retry dirty:", dirty)
        isolate_layers(job, ids=dirty, workers=args.workers, force=True, skip_bg=True)
        compose(job, scale=args.scale)
        run_gate(job)
        ghost_qa(job, scale=args.scale)
        return 0

    if args.command == "run-local":
        # no API — setup + bg + compose(if sprites exist) + gate + qa + emit
        setup_and_calibrate(job, skip_match=args.skip_match)
        build_local_background(job)
        # if new/ has other sprites, compose
        compose(job, scale=args.scale)
        run_gate(job)
        try:
            ghost_qa(job, scale=args.scale)
        except Exception as e:
            print("qa skip:", e)
        emit_html(job, title=args.title or None)
        return 0

    if args.command == "pipeline":
        setup_and_calibrate(job, skip_match=args.skip_match)
        local_bg = _use_local_bg(args)
        if local_bg:
            build_local_background(job)
        isolate_layers(
            job,
            workers=args.workers,
            force=args.force,
            skip_bg=local_bg,
            dry_run=args.dry_run,
        )
        if args.dry_run:
            return 0
        compose(job, scale=args.scale)
        st = run_gate(job)
        for round_i in range(args.max_rounds):
            dirty = st.get("dirty_ids") or []
            if not dirty:
                break
            print(f"pipeline retry round {round_i+1}: {dirty}")
            isolate_layers(job, ids=dirty, workers=args.workers, force=True, skip_bg=True)
            compose(job, scale=args.scale)
            st = run_gate(job)
        ghost_qa(job, scale=args.scale)
        emit_html(job, title=args.title or None)
        return 0

    print("unknown command", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
