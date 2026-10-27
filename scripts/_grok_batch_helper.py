#!/usr/bin/env python3
"""Helper: dump next-jobs / status for opt1027 skill converge without console mojibake."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

import run_v8_20_skill_converge_grok as grok  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=("next-jobs", "status", "ingest"))
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--limit", type=int, default=4)
    ap.add_argument("--bot-id", default="")
    ap.add_argument("--round", type=int, default=0)
    ap.add_argument("--image", default="")
    ap.add_argument("--dump", default="")
    args = ap.parse_args()

    class NS:
        pass

    ns = NS()
    ns.out_dir = args.out_dir
    ns.limit = args.limit
    ns.bot_id = args.bot_id
    ns.round = args.round
    ns.image = args.image
    ns.error = ""
    # defaults required by grok.main parsers for other cmds
    ns.threshold = 9.6
    ns.anat_gate = 7.5
    ns.max_rounds = 8
    ns.pad = "auto"
    ns.drop_stop = 0.5
    ns.early_stop_min_round = 4
    ns.drop_streak = 2
    ns.concurrency = 4
    ns.limit_bots = 0
    ns.only = ""
    ns.env = ""
    ns.score_model = "gpt-6-sol"
    ns.score_backend = "offline"

    if args.command == "next-jobs":
        # capture print
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = grok.next_jobs(ns)
        text = buf.getvalue()
        dump = Path(args.dump) if args.dump else Path(args.out_dir) / "_jobs_batch.json"
        dump.write_text(text, encoding="utf-8")
        data = json.loads(text)
        brief = {
            "ok": data.get("ok"),
            "counts": data.get("counts"),
            "jobs": [
                {
                    "bot_id": j["bot_id"],
                    "round": j["round"],
                    "aspect_ratio": j["aspect_ratio"],
                    "pad_src": j.get("pad_src"),
                    "gen_filename": j["gen_filename"],
                    "out_path": j["out_path"],
                    "prompt": j["prompt"],
                }
                for j in data.get("jobs") or []
            ],
        }
        print(json.dumps(brief, ensure_ascii=False, indent=2))
        return code

    if args.command == "status":
        state = grok.load_json(Path(args.out_dir) / grok.STATE_NAME, {})
        bots = state.get("bots") or {}
        summary = {
            "active": sum(1 for s in bots.values() if s.get("status") == "active"),
            "done": sum(1 for s in bots.values() if s.get("status") == "done"),
            "failed": sum(1 for s in bots.values() if s.get("status") == "failed"),
            "bots": {
                bid: {
                    "status": st.get("status"),
                    "next_round": st.get("next_round"),
                    "rounds_done": len(st.get("rounds") or []),
                    "best_total": (st.get("best_round") or {}).get("total"),
                    "stop_reason": st.get("stop_reason"),
                }
                for bid, st in bots.items()
            },
        }
        dump = Path(args.dump) if args.dump else Path(args.out_dir) / "_status.json"
        dump.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        started = [f"{bid} R{v['rounds_done']} next={v['next_round']} best={v['best_total']} {v['status']}" for bid, v in summary["bots"].items() if v["rounds_done"] > 0]
        print(f"active={summary['active']} done={summary['done']} started={len(started)}")
        for line in started:
            print(line)
        return 0

    if args.command == "ingest":
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            code = grok.ingest(ns)
        print(buf.getvalue())
        return code

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
