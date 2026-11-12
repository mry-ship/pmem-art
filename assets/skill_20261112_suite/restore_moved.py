# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SUITE = ROOT / "assets" / "skill_20261112_suite" / "out"
LOG = SUITE / "atlas.file" / "classify-watch.txt"
TERM = Path(
    r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\terminals\23812.txt"
)


def parse_moves(text: str) -> list[tuple[str, str]]:
    moves: list[tuple[str, str]] = []
    for m in re.finditer(r'"from":\s*"([^"]+)".*?"to":\s*"([^"]+)"', text, re.S):
        fr, to = m.group(1), m.group(2)
        if "skill_20261112_suite" in fr.replace("\\", "/"):
            moves.append((fr.replace("\\", "/"), to.replace("\\", "/")))
    return moves


def main() -> None:
    texts: list[str] = []
    for p in (LOG, TERM):
        if p.exists():
            texts.append(p.read_text(encoding="utf-8", errors="replace"))
    moves: list[tuple[str, str]] = []
    for t in texts:
        moves.extend(parse_moves(t))
    # dedupe keep last
    last: dict[str, str] = {}
    for fr, to in moves:
        last[fr] = to
    print(f"unique moves from suite: {len(last)}")
    restored = 0
    missing_src = 0
    for fr, to in sorted(last.items()):
        src = ROOT / to
        dst = ROOT / fr
        if not src.exists():
            # maybe already relative weirdness
            alt = Path(to)
            if not alt.is_absolute():
                alt = ROOT / alt
            src = alt
        if not src.exists():
            print(f"MISSING SRC {to} (for {fr})")
            missing_src += 1
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            print(f"keep existing {fr}")
            continue
        shutil.copy2(src, dst)
        restored += 1
        print(f"restored {fr} <- {to}")
    print(f"restored={restored} missing_src={missing_src}")


if __name__ == "__main__":
    main()
