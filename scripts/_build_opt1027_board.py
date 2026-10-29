#!/usr/bin/env python3
"""Build manifest + index for opt1027 20-image board, then score."""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "docs" / "showcase" / "rerun_5scale_opt1027"
sys.path.insert(0, str(REPO / "scripts"))

CASE_CN = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}
LABEL_CN = {
    "low_best": "low · 只修瑕",
    "medium_best": "medium · 锁机位小优化",
    "high_best": "high · 跃升",
    "recompose": "recompose · 改机位",
    "recompose_bold": "大改 · 风格跳",
}
SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
SHORT = {
    "low_best": "low",
    "medium_best": "medium",
    "high_best": "high",
    "recompose": "recompose",
    "recompose_bold": "bold",
}


def main() -> int:
    jobs = json.loads((BOARD / "jobs.json").read_text(encoding="utf-8"))
    rows = []
    for j in jobs:
        out = BOARD / "images" / j["out_name"]
        # accept .png even if source was jpg copy
        ok = out.is_file() and out.stat().st_size > 1000
        rows.append(
            {
                "bot_id": j["bot_id"],
                "slug": j["slug"],
                "case": CASE_CN[j["slug"]],
                "display_scale": j["scale"],
                "label": LABEL_CN[j["scale"]],
                "file": f"images/{j['out_name']}" if ok else "",
                "ok": ok,
                "error": "" if ok else "missing",
                "prompt": j["prompt"],
                "aspect_ratio": j["aspect"],
                "ref": str(Path(j["ref"]).relative_to(REPO)).replace("\\", "/"),
            }
        )
    (BOARD / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    ok_n = sum(1 for r in rows if r["ok"])
    print(f"manifest {ok_n}/{len(rows)}")

    # lightweight preview HTML before scoring
    by = {}
    for r in rows:
        by.setdefault(r["slug"], []).append(r)
    sections = []
    for slug in CASE_CN:
        items = sorted(by.get(slug, []), key=lambda x: SCALE_ORDER.index(x["display_scale"]))
        ref = f"images/{slug}_ref.png"
        cards = [f'<figure class="card ref"><figcaption>原图</figcaption><img src="{ref}"></figure>']
        for it in items:
            if it["ok"]:
                body = f'<img src="{it["file"]}" alt="{it["label"]}">'
            else:
                body = '<p class="err">缺失</p>'
            cards.append(
                f'<figure class="card"><figcaption>{it["label"]}</figcaption>{body}'
                f'<details><summary>提示词</summary><p>{it["prompt"].replace("<","&lt;")}</p></details></figure>'
            )
        sections.append(f'<section><h2>{CASE_CN[slug]}</h2><div class="row">{"".join(cards)}</div></section>')
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>优化后重出 · 20 张五档</title>
<style>
body{{margin:0;background:#141414;color:#eee;font-family:"Segoe UI",sans-serif}}
header{{padding:24px 28px 8px}} h1{{font-size:22px;margin:0 0 8px}}
p.note{{color:#aaa;max-width:980px;line-height:1.5}}
section{{padding:8px 20px 28px}} h2{{font-size:16px;margin:12px 8px}}
.row{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}}
.card{{margin:0;background:#1e1e1e;border:1px solid #333;padding:8px}}
.card.ref{{border-color:#6a5a3a}} figcaption{{font-size:12px;margin-bottom:6px;color:#ddd}}
img{{width:100%;height:auto;display:block;background:#0e0e0e}}
details{{margin-top:6px;font-size:11px;color:#9a9a9a}} details p{{white-space:pre-wrap}}
.err{{color:#f0a0a0;font-size:12px}}
</style></head><body>
<header>
<h1>案例 01–04 · 今日优化后重出（20 张）</h1>
<p class="note">2026-10-27：用今日 skills_kit 档位合同（strip_affirmative_locks / compose_style_first_prompt）重出。
因 apikey.fan 生图额度不足，生图改走 Cursor GenerateImage（垫风格参考）。每格 1 轮，便于横看 low/medium/high/recompose/bold。
评分稍后写入。旧板：docs/showcase/rerun_5scale/ · V8 多轮板：pmem_art_images_v8_20bots_showcase.html</p>
</header>
{''.join(sections)}
</body></html>"""
    (BOARD / "index.html").write_text(html, encoding="utf-8")
    print("wrote", BOARD / "index.html")
    return 0 if ok_n == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
