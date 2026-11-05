#!/usr/bin/env python3
"""Windows Shell preToolUse：把 python/python3 改成 pyw，且必须极轻（不可 import pmem_art）。"""
from __future__ import annotations

import json
import sys

from art_cli import rewrite_shell_to_windowless


def main() -> int:
    payload: dict = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            payload = json.loads(raw)
    except Exception:
        payload = {}
    args = payload.get("tool_input") or payload.get("arguments") or payload.get("args") or {}
    if not isinstance(args, dict):
        args = {}
    cmd = str(args.get("command") or args.get("cmd") or "")
    rewritten = rewrite_shell_to_windowless(cmd)
    out: dict = {
        "continue": True,
        "server": "pmem-art",
        "event": "pre-shell",
        "agentMessage": "",
    }
    if rewritten is not None:
        new_args = dict(args)
        if "command" in new_args or "cmd" not in new_args:
            new_args["command"] = rewritten
        if "cmd" in args:
            new_args["cmd"] = rewritten
        out["updated_input"] = new_args
        out["permission"] = "allow"
    sys.stdout.write(json.dumps(out, ensure_ascii=False))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
