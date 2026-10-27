#!/usr/bin/env python3
"""Rewrite rerun_5scale_opt1027/index.html from skill converge state (real rounds)."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STATE = REPO / "generated_v8_20_skill_opt1027" / "orchestrator_state.json"
BOARD = REPO / "docs" / "showcase" / "rerun_5scale_opt1027"
IMG = BOARD / "images" / "skill"
CASE = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}
SCALE_CN = {
    "low_best": "low · 只修瑕",
    "medium_best": "medium · 锁机位小优化",
    "high_best": "high · 跃升",
    "recompose": "recompose · 改机位",
    "recompose_bold": "大改 · 风格跳",
}
ORDER = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]


def main() -> int:
    state = json.loads(STATE.read_text(encoding="utf-8"))
    IMG.mkdir(parents=True, exist_ok=True)
    by_case: dict[str, list] = {k: [] for k in ORDER}
    started = 0
    for bid, st in state["bots"].items():
        bot = st["bot"]
        slug = bot["slug"]
        rounds = st.get("rounds") or []
        cells = []
        for rec in rounds:
            src = REPO / "generated_v8_20_skill_opt1027" / rec["filename"]
            if not src.is_file():
                continue
            dst = IMG / rec["filename"]
            shutil.copy2(src, dst)
            cells.append(
                {
                    "round": rec["round"],
                    "total": rec.get("total"),
                    "src": f"images/skill/{rec['filename']}",
                    "best": bool((st.get("best_round") or {}).get("round") == rec["round"]),
                }
            )
        if cells:
            started += 1
        by_case.setdefault(slug, []).append(
            {
                "bid": bid,
                "scale": bot.get("display_scale"),
                "label": SCALE_CN.get(bot.get("display_scale"), bot.get("display_scale")),
                "status": st.get("status"),
                "next": st.get("next_round"),
                "stop": st.get("stop_reason"),
                "best": (st.get("best_round") or {}).get("total"),
                "n": len(cells),
                "cells": cells,
            }
        )

    sections = []
    for slug in ORDER:
        items = sorted(by_case.get(slug) or [], key=lambda x: SCALE_ORDER.index(x["scale"]) if x["scale"] in SCALE_ORDER else 99)
        blocks = []
        for it in items:
            if not it["cells"]:
                blocks.append(
                    f'<article class="bot wait"><h3>{it["label"]}</h3>'
                    f'<p class="meta">{it["bid"]} · skill 闭环尚未开跑（不是第 1 轮终稿）</p></article>'
                )
                continue
            cards = []
            for c in it["cells"]:
                mark = " · 当前最高" if c["best"] else ""
                cls = "mid" if (c["total"] or 0) >= 8.5 else "low"
                cards.append(
                    f'<figure><figcaption>第{c["round"]}轮{mark}</figcaption>'
                    f'<div class="shot"><span class="total {cls}">{c["total"]}</span>'
                    f'<img src="{c["src"]}" alt="R{c["round"]}"></div></figure>'
                )
            nxt = f'下一轮 R{it["next"]}' if it["status"] == "active" else (it["stop"] or it["status"])
            blocks.append(
                f'<article class="bot"><h3>{it["label"]} · 已跑 {it["n"]} 轮</h3>'
                f'<p class="meta">{it["bid"]} · best {it["best"]} · {nxt}</p>'
                f'<div class="rounds">{"".join(cards)}</div></article>'
            )
        sections.append(f'<section><h2>{CASE[slug]}</h2>{"".join(blocks)}</section>')

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Skill 闭环进度 · 真实轮次</title>
<style>
body{{margin:0;background:#141414;color:#eee;font-family:"Segoe UI","PingFang SC",sans-serif}}
header{{padding:24px 28px 8px}} h1{{font-size:22px;margin:0 0 8px}}
p.note{{color:#aaa;max-width:1100px;line-height:1.5}}
section{{padding:8px 20px 24px}} h2{{font-size:16px;margin:8px}}
.bot{{background:#1e1e1e;border:1px solid #333;border-radius:10px;margin:10px 8px;padding:12px}}
.bot.wait{{opacity:.72}}
h3{{margin:0 0 4px;font-size:14px}}
.meta{{margin:0 0 8px;color:#9a9a9a;font-size:12px}}
.rounds{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px}}
figure{{margin:0}} figcaption{{font-size:12px;margin-bottom:4px}}
.shot{{position:relative}}
.total{{position:absolute;top:6px;left:6px;background:rgba(0,0,0,.65);padding:2px 6px;border-radius:4px;font-weight:650}}
.total.mid{{color:#e6c36a}} .total.low{{color:#e0a0a0}}
img{{width:100%;display:block;background:#0e0e0e}}
</style></head><body>
<header>
<h1>案例 01–04 · Skill 闭环真实轮次</h1>
<p class="note">这页替换了早先「20 张都标第 1 轮」的单轮板。数字来自 generated_v8_20_skill_opt1027 编排器：合同 ≤8 轮、合格线 ≥9.6。目前 {started}/20 个 bot 已进入闭环，各跑到第 4 轮，下一轮是第 5 轮。其余 16 个还没开跑，所以不再把旧单轮图标成第 1 轮终稿。分数是离线 Absolute-5D 旁证。</p>
</header>
{''.join(sections)}
</body></html>"""
    out = BOARD / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out} started={started}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
