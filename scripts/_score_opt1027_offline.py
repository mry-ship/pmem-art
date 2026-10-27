#!/usr/bin/env python3
"""Offline Absolute-5D advisory scores for opt1027 board (no API key)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "docs" / "showcase" / "rerun_5scale_opt1027"
sys.path.insert(0, str(REPO / "scripts"))

from absolute_5d_scorer import absolute_5d  # noqa: E402

SCALE_TO_API = {
    "low_best": "low",
    "medium_best": "medium",
    "high_best": "high",
    "recompose": "recompose",
    "recompose_bold": "recompose",
    "ref": "medium",
}


def main() -> int:
    rows = json.loads((BOARD / "manifest.json").read_text(encoding="utf-8"))
    scores: dict[str, dict] = {}
    # refs
    for slug in ("night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"):
        p = BOARD / "images" / f"{slug}_ref.png"
        if not p.is_file():
            continue
        print(f"OFFLINE {p.name}", flush=True)
        h = absolute_5d(str(p), api_scale="medium")
        scores[p.name] = {
            "ok": True,
            "model": "offline_absolute_5d_v9.1",
            "dims": h.get("dims") or {},
            "defects": (h.get("issues") or h.get("defects") or [])[:3],
            "strengths": [],
            "offline_total": h.get("score"),
        }
    for r in rows:
        if not r.get("ok"):
            continue
        name = Path(r["file"]).name
        p = BOARD / "images" / name
        api = SCALE_TO_API.get(r["display_scale"], "medium")
        print(f"OFFLINE {name} api={api}", flush=True)
        h = absolute_5d(str(p), api_scale=api)
        scores[name] = {
            "ok": True,
            "model": "offline_absolute_5d_v9.1",
            "dims": h.get("dims") or {},
            "defects": (h.get("issues") or h.get("defects") or [])[:3],
            "strengths": [],
            "offline_total": h.get("score"),
            "display_scale": r["display_scale"],
        }
    (BOARD / "offline_scores.json").write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # patch index with score pills
    DIMS = (
        "composition",
        "lighting_color",
        "perspective_anatomy",
        "texture_detail",
        "spec_style",
    )
    WEIGHTS = {
        "low_best": {"composition": 0.15, "lighting_color": 0.20, "perspective_anatomy": 0.25, "texture_detail": 0.25, "spec_style": 0.15},
        "medium_best": {"composition": 0.20, "lighting_color": 0.25, "perspective_anatomy": 0.20, "texture_detail": 0.20, "spec_style": 0.15},
        "high_best": {"composition": 0.15, "lighting_color": 0.30, "perspective_anatomy": 0.15, "texture_detail": 0.20, "spec_style": 0.20},
        "recompose": {"composition": 0.30, "lighting_color": 0.20, "perspective_anatomy": 0.20, "texture_detail": 0.15, "spec_style": 0.15},
        "recompose_bold": {k: 0.2 for k in DIMS},
        "ref": {k: 0.2 for k in DIMS},
    }

    def total(dims: dict, scale: str) -> float:
        w = WEIGHTS.get(scale, {k: 0.2 for k in DIMS})
        return round(sum(float(dims.get(k, 0)) * w[k] for k in DIMS), 2)

    CASE_CN = {
        "night_city": "案例 01 · 仙侠不夜城",
        "pastel_sketch": "案例 02 · 粉彩速写少女",
        "sunlit_portrait": "案例 03 · 窗边日光胸像",
        "ishtar_canyon": "案例 04 · 天井峡谷概念",
    }
    SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
    by = {}
    for r in rows:
        by.setdefault(r["slug"], []).append(r)
    totals = []
    sections = []
    for slug in CASE_CN:
        items = sorted(by.get(slug, []), key=lambda x: SCALE_ORDER.index(x["display_scale"]))
        cards = []
        ref_name = f"{slug}_ref.png"
        sc = scores.get(ref_name) or {}
        dims = sc.get("dims") or {}
        t = total(dims, "ref") if dims else None
        if t is not None:
            totals.append(t)
        dim_line = " · ".join(f"{k[0]}{dims[k]}" for k in DIMS if k in dims) if dims else "—"
        cards.append(
            f'<figure class="card ref"><figcaption>原图</figcaption>'
            f'<div class="shot"><span class="total">{t if t is not None else "—"}</span>'
            f'<img src="images/{ref_name}"></div>'
            f'<p class="extra">原图 · 离线旁证 · {dim_line}</p></figure>'
        )
        for it in items:
            name = Path(it["file"]).name if it.get("file") else ""
            sc = scores.get(name) or {}
            dims = sc.get("dims") or {}
            t = total(dims, it["display_scale"]) if dims else None
            if t is not None:
                totals.append(t)
            cls = "hit" if t is not None and t >= 9.6 else ("mid" if t is not None and t >= 8.5 else "low")
            dim_line = " · ".join(f"{k[0]}{dims[k]}" for k in DIMS if k in dims) if dims else "—"
            body = f'<img src="{it["file"]}">' if it.get("ok") else '<p class="err">缺失</p>'
            cards.append(
                f'<figure class="card"><figcaption>{it["label"]}</figcaption>'
                f'<div class="shot"><span class="total {cls}">{t if t is not None else "—"}</span>{body}</div>'
                f'<p class="extra">离线旁证 · {dim_line}</p>'
                f'<details><summary>提示词</summary><p>{it["prompt"].replace("<","&lt;")}</p></details></figure>'
            )
        sections.append(f'<section><h2>{CASE_CN[slug]}</h2><div class="row">{"".join(cards)}</div></section>')

    mean = round(sum(totals) / len(totals), 2) if totals else None
    gen_n = sum(1 for r in rows if r.get("ok"))
    note = (
        "完整对照：4 个案例 × 原图 + low / medium / high / recompose / 大改，共 20 张。"
        "后补的 skill 多轮只跑了 4 路、各 4 轮，离线分停在 7.7–8.5，没有超过这批图，所以主板仍用这 20 张。"
        "分数是离线 Absolute-5D 旁证，不是 VLM 盲评。"
        + (f" 旁证均分 {mean:.2f}（含原图 n={len(totals)}）。" if mean is not None else "")
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>优化后重出 · 20 张五档</title>
<style>
body{{margin:0;background:#141414;color:#eee;font-family:"Segoe UI",sans-serif}}
header{{padding:24px 28px 8px}} h1{{font-size:22px;margin:0 0 8px}}
p.note{{color:#aaa;max-width:1100px;line-height:1.5}}
section{{padding:8px 20px 28px}} h2{{font-size:16px;margin:12px 8px}}
.row{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}}
.card{{margin:0;background:#1e1e1e;border:1px solid #333;padding:8px}}
.card.ref{{border-color:#6a5a3a}} figcaption{{font-size:12px;margin-bottom:6px;color:#ddd}}
.shot{{position:relative}} .total{{position:absolute;top:8px;left:8px;z-index:1;font-variant-numeric:tabular-nums;font-weight:650;background:rgba(0,0,0,.62);padding:2px 7px;border-radius:4px}}
.total.hit{{color:#8fd18f}} .total.mid{{color:#e6c36a}} .total.low{{color:#e0a0a0}}
img{{width:100%;height:auto;display:block;background:#0e0e0e}}
.extra{{margin:6px 0 0;font-size:11px;color:#c8c8c8;line-height:1.35}}
details{{margin-top:6px;font-size:11px;color:#9a9a9a}} details p{{white-space:pre-wrap}}
.err{{color:#f0a0a0;font-size:12px}}
</style></head><body>
<header>
<h1>案例 01–04 · 五档对照（20 张）</h1>
<p class="note">{note}</p>
</header>
{''.join(sections)}
</body></html>"""
    (BOARD / "index.html").write_text(html, encoding="utf-8")
    print("mean", mean, "n", len(totals), "->", BOARD / "index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
