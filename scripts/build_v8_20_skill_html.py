#!/usr/bin/env python3
"""Build V8-20-v2 showcase HTML matching v6 layout/CSS (case-block, five-col-grid, legends)."""
from __future__ import annotations

import argparse
import base64
import csv
import json
import mimetypes
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

CASE_CN = {
    "night_city": "东方仙侠不夜城 · 飞檐孤侠俯瞰万家灯火",
    "pastel_sketch": "油画棒粉彩速写 · 红卫衣屈膝少女",
    "sunlit_portrait": "胶片轻厚涂肖像 · 二分光雏菊壁纸",
    "ishtar_canyon": "概念厚涂峡谷 · Ishtar 天井飞龙",
}
CASE_REF = {
    "night_city": ("style_ref_01_night_city.png", "9:16"),
    "pastel_sketch": ("style_ref_02_pastel_sketch.png", "4:3"),
    "sunlit_portrait": ("style_ref_03_sunlit_portrait.png", "3:4"),
    "ishtar_canyon": ("web_ref_01_concept_ishtar.png", "4:3"),
}
SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
SCALE_BADGE = {
    "low_best": ("低·最优方向", "pmode-boost", "boost"),
    "medium_best": ("中·最优方向", "pmode-boost", "boost"),
    "high_best": ("高·最优方向", "pmode-boost", "boost"),
    "recompose": ("改构图", "pmode-none", "auto"),
    "recompose_bold": ("大改 bold", "pmode-bold", "bold"),
    "baseline": ("原图 Baseline", "pmode-baseline", "ref"),
}
DIMS = ("composition", "lighting_color", "perspective_anatomy", "texture_detail", "spec_style")
DIM_CN = {
    "composition": "构图",
    "lighting_color": "光影",
    "perspective_anatomy": "透视",
    "texture_detail": "质感",
    "spec_style": "风格",
}


def mean(xs):
    xs = [x for x in xs if x is not None]
    return round(sum(xs) / len(xs), 2) if xs else None


def data_uri(path: Path) -> str:
    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def load_scores(path: Path) -> dict:
    raw = json.loads(path.read_text())
    images = raw.get("images") or raw
    out = {}
    for k, v in images.items():
        if not isinstance(v, dict):
            continue
        fn = v.get("filename") or Path(k).name
        # prefer nested total
        total = v.get("total")
        if total is None and isinstance(v.get("score"), dict):
            total = v["score"].get("total")
        dims = v.get("dims") or (v.get("score") or {}).get("dims") or {}
        grade = v.get("grade") or (v.get("score") or {}).get("grade") or ""
        defects = v.get("defects") or (v.get("score") or {}).get("defects") or []
        role = v.get("role") or ""
        out[fn] = {
            "total": total,
            "dims": dims,
            "grade": grade,
            "defects": defects,
            "role": role,
            "ok": v.get("ok", True),
            "filename": fn,
        }
    return out


def rounds_from_manifest(manifest: dict) -> dict[str, dict]:
    items = manifest.get("items") or {}
    out = {}
    for bid, rec in items.items():
        rounds = rec.get("rounds") or []
        n = len(rounds)
        if rec.get("skipped"):
            label = "跳过·0轮"
        elif n == 0:
            label = "轮次N/A"
        elif n == 1:
            label = "R1·1轮"
        else:
            label = f"R1→R{n}·{n}轮"
        stop = rec.get("stop_reason") or ""
        sc = rec.get("final_score")
        if stop:
            label = f"{label} · {stop}"
        if isinstance(sc, (int, float)):
            label = f"{label} · {sc:.2f}"
        out[bid] = {"n": n, "label": label, "rounds": rounds}
    return out


def card_html(*, badge, pmode_cls, src, filename, total, grade, dims, defects, rounds_label, kind, r1_src=None, r1_total=None, r1_filename=None):
    dim_txt = " · ".join(f"{DIM_CN[d]} {dims.get(d, '—')}" for d in DIMS if dims)
    def_txt = "；".join((defects or [])[:3])
    score_txt = f"{total:.2f}" if isinstance(total, (int, float)) else "—"
    landscape = " landscape" if any(x in filename for x in ("pastel", "ishtar", "4_3", "web_ref")) else ""
    bar = {
        "boost": "pmode-boost-bar",
        "bold": "pmode-bold-bar",
        "auto": "pmode-none-bar",
        "ref": "pmode-none-bar",
    }.get(kind, "pmode-none-bar")
    ref_cls = " ref-card" if kind == "ref" else ""
    source = "原图 Baseline" if kind == "ref" else "gpt-image-2 · V8→V2 · 终图"
    source_cls = "ref-source" if kind == "ref" else "auto-source"
    r1_block = ""
    if r1_src:
        r1_score = f"{r1_total:.2f}" if isinstance(r1_total, (int, float)) else "—"
        r1_block = f"""
  <div class="source-tag" style="background:rgba(148,163,184,.15);color:#cbd5e1;border:1px solid rgba(148,163,184,.4);margin-top:4px">R1 中间轮 · {r1_score}</div>
  <div class="img-wrap{landscape}" style="aspect-ratio:inherit;max-height:220px"><img src="{r1_src}" alt="{r1_filename or 'r1'}" loading="lazy"></div>
  <div class="hash-tag">{r1_filename or ''}</div>"""
    return f"""
<div class="col-card{ref_cls}">
  <span class="pmode-tag {pmode_cls}">{badge}</span>
  <span class="pmode-bar {bar}"></span>
  <div class="source-tag {source_cls}">{source}</div>
  <div class="img-wrap{landscape}"><img src="{src}" alt="{filename}" loading="lazy"></div>
  <div class="score-line"><span class="score-pill ref-pill">{score_txt}</span><span class="hash-tag">{grade or ''}</span></div>
  <div class="mini-badge">{rounds_label}</div>
  <div class="dims-line">{dim_txt or '—'}</div>
  <div class="col-desc" style="color:#fda4af;font-size:11px">{def_txt}</div>
  <div class="hash-tag">{filename}</div>{r1_block}
</div>"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--img-dir", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prev-mean", type=float, default=8.06)
    ap.add_argument("--embed", action="store_true")
    ap.add_argument("--href-prefix", default="")
    args = ap.parse_args()

    img_dir = Path(args.img_dir)
    scores = load_scores(Path(args.scores))
    manifest = json.loads(Path(args.manifest).read_text()) if Path(args.manifest).is_file() else {"items": {}}
    rounds_map = rounds_from_manifest(manifest)
    thr = float((manifest.get("threshold") if isinstance(manifest, dict) else None) or 9.5)
    items = (manifest.get("items") or {}) if isinstance(manifest, dict) else {}
    ok_items = [r for r in items.values() if r.get("ok")]
    n_reached = sum(1 for r in ok_items if float(r.get("final_score") or 0) >= thr)
    from collections import Counter
    stop_reasons = dict(Counter(str(r.get("stop_reason")) for r in ok_items))
    skill_round_dist = dict(Counter(int(r.get("n_rounds") or 0) for r in ok_items))
    selection = json.loads((img_dir / "selection.json").read_text()) if (img_dir / "selection.json").is_file() else {}

    style = Path("/workspace/pmem-art-v8/_latest_desktop/v6_showcase_style.css").read_text()

    # Collect bots by slug
    by_slug: dict[str, dict[str, dict]] = defaultdict(dict)
    bot_totals = []
    round_counts = defaultdict(int)
    grade_dist = defaultdict(int)

    for fn, sc in scores.items():
        if sc.get("role") == "baseline" or fn.startswith("style_ref_") or fn.startswith("web_ref_"):
            continue
        # parse v8_bot_XX_slug_scale
        parts = fn.rsplit(".", 1)[0].split("_")
        # v8_bot_02_night_city_low_best
        if not fn.startswith("v8_bot_"):
            continue
        # find display_scale
        display = None
        slug = None
        bot_id = None
        for scale in SCALE_ORDER:
            token = f"_{scale}"
            if fn.rsplit(".", 1)[0].endswith(scale) or f"_{scale}." in fn or f"_{scale}_r" in fn:
                # skip round intermediates in main grid
                if "_r" in fn.rsplit(".", 1)[0].split(scale)[-1]:
                    display = None
                    break
                display = scale
                stem = fn.rsplit(".", 1)[0]
                # stem = v8_bot_02_night_city_low_best
                core = stem[: -len(scale) - 1]  # v8_bot_02_night_city
                bits = core.split("_")
                bot_id = "_".join(bits[:3])  # v8_bot_02
                slug = "_".join(bits[3:])
                break
        if not display or not slug:
            continue
        by_slug[slug][display] = {"filename": fn, "score": sc, "bot_id": bot_id, "path": img_dir / fn}
        if isinstance(sc.get("total"), (int, float)):
            bot_totals.append(sc["total"])
            grade_dist[sc.get("grade") or "未知"] += 1
        rinfo = rounds_map.get(bot_id or "") or {}
        n = rinfo.get("n", 0)
        round_counts[f"{n}轮" if n else "轮次N/A"] += 1

    # baselines
    baselines = []
    for slug, (fn, ar) in CASE_REF.items():
        path = img_dir / fn
        if not path.is_file():
            for alt in (
                Path("/workspace/pmem-art-v8/comparison/style_refs") / fn,
                Path("/workspace/pmem-art-v8/comparison/web_refs") / fn,
            ):
                if alt.is_file():
                    path = alt
                    break
        sc = scores.get(fn) or {}
        baselines.append({"slug": slug, "filename": fn, "ar": ar, "path": path, "score": sc})
    base_totals = [b["score"]["total"] for b in baselines if isinstance(b["score"].get("total"), (int, float))]

    now = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M Asia/Shanghai (UTC+8)")
    v_mean = mean(bot_totals)
    delta = round(v_mean - args.prev_mean, 2) if v_mean is not None else None
    base_mean = mean(base_totals)
    dim_means = {}
    for d in DIMS:
        vals = []
        for slug_map in by_slug.values():
            for rec in slug_map.values():
                v = (rec["score"].get("dims") or {}).get(d)
                if isinstance(v, (int, float)):
                    vals.append(v)
        dim_means[d] = mean(vals)

    def src_for(path: Path, fn: str) -> str:
        if args.embed and path.is_file():
            return data_uri(path)
        pref = args.href_prefix
        return f"{pref}{fn}" if pref or path.parent == img_dir else str(path)

    parts = []
    parts.append(f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>pmem-art · V8×20 Bot Showcase (skills_kit · ≥9.50 / 8 rounds)</title>
<style>
{style}
.score-big{{font-size:22px;font-weight:800}}
.stats-row{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-top:14px}}
.stat{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.1);border-radius:12px;padding:12px}}
.stat .k{{font-size:12px;color:var(--muted)}}
.stat .v{{font-size:22px;font-weight:800;margin-top:4px}}
.up{{color:#4ade80}}.down{{color:#fb7185}}.flat{{color:#94a3b8}}
@media(max-width:1100px){{.stats-row{{grid-template-columns:1fr 1fr}}}}
.five-col-grid.base-grid{{grid-template-columns:repeat(4,minmax(0,1fr))}}
</style></head><body>
<header>
<h1>🎨 pmem-art · V8 × 20 Bot 展陈（skills_kit 合同 · STOP≥9.50 · 最多8轮）</h1>
<p>选型：4 风格 ×（low_best / medium_best / high_best / recompose / recompose_bold）= 20（与前次相同）。生图：gpt-image-2 edits（自 style ref）；按 skills_kit：停分 ≥9.50、上限 8 轮、缺陷回流再生成。评分：gpt-6-sol Absolute-5D Quant。布局对齐 <code>pmem_art_images_v6_32bots_showcase.html</code>（category legend · case-block · five-col-grid · baseline）。旧 V2 showcase 剧本分不可横比。</p>
<div class="category-legend">
  <div class="legend-box legend-auto"><b>改构图 recompose</b><br>跟 --recompose-dir 换机位；保画风色板与身份；≥2 轮</div>
  <div class="legend-box legend-boost"><b>最优方向 best</b><br>low/med/high + cinematic V8 加法清单（孔明灯/耳机/雏菊/体积光）</div>
  <div class="legend-box legend-bold"><b>大改 recompose_bold</b><br>仅剪影+画幅+风格圣经大跳；禁止混装保色板/旧机位</div>
</div>
<div class="rule-pills">
  <span class="rule-pill">评分 gpt-6-sol Quant</span>
  <span class="rule-pill">生图 gpt-image-2</span>
  <span class="rule-pill">STOP ≥9.50 · max 8</span>
  <span class="rule-pill">前次 V8-20 均值 {args.prev_mean}</span>
  <span class="rule-pill">轮次 {' · '.join(f'{k}×{v}' for k,v in sorted(round_counts.items())) or '—'}</span>
  <span class="rule-pill">更新 {now}</span>
</div>
<div class="stats-row">
  <div class="stat"><div class="k">V8-v2 均值 (n={len(bot_totals)})</div><div class="v">{v_mean if v_mean is not None else '—'}</div></div>
  <div class="stat"><div class="k">vs 前次 V8-20 {args.prev_mean}</div><div class="v {'up' if (delta or 0)>0 else 'down' if (delta or 0)<0 else 'flat'}">{('+' if delta and delta>0 else '')}{delta if delta is not None else '—'}</div></div>
  <div class="stat"><div class="k">原图基线均值</div><div class="v">{base_mean if base_mean is not None else '—'}</div></div>
  <div class="stat"><div class="k">区间</div><div class="v">{f"{min(bot_totals):.2f}–{max(bot_totals):.2f}" if bot_totals else '—'}</div></div>
  <div class="stat"><div class="k">≥9.50 达标</div><div class="v">{n_reached}/{len(ok_items)}</div></div>
</div>
<p style="margin-top:10px;font-size:13px;color:#cbd5e1">停因 {stop_reasons} · 轮次分布 {skill_round_dist} · 合同停分 {thr}</p>
<p style="margin-top:12px;font-size:13px;color:#cbd5e1">维度均值：{' · '.join(f'{DIM_CN[d]} {dim_means.get(d)}' for d in DIMS)}</p>
</header>
""")

    # Baseline section
    parts.append('<section class="case-block"><div class="case-header"><div><span class="case-tag">baselines</span><h2>原图 / 风格参考（Absolute-5D 同尺）</h2></div><div class="case-meta">4 refs · 与 bot 同一 gpt-6-sol Quant 量表</div></div>')
    parts.append('<div class="five-col-grid base-grid">')
    for b in baselines:
        sc = b["score"]
        badge, pcls, kind = SCALE_BADGE["baseline"]
        src = src_for(b["path"], b["filename"]) if b["path"].is_file() else ""
        parts.append(card_html(
            badge=f"{badge} · {b['slug']}",
            pmode_cls=pcls,
            src=src,
            filename=b["filename"],
            total=sc.get("total"),
            grade=sc.get("grade") or "",
            dims=sc.get("dims") or {},
            defects=sc.get("defects") or [],
            rounds_label="原图·0轮",
            kind="ref",
        ))
    parts.append("</div></section>")

    # Per-case grids
    for slug in ("night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"):
        ref_fn, ar = CASE_REF[slug]
        parts.append(f'''<section class="case-block">
<div class="case-header"><div><span class="case-tag">{slug}</span>
<h2>案例 · {CASE_CN.get(slug, slug)} ({ref_fn})</h2></div>
<div class="case-meta">画幅 <code>{ar}</code> · 5 档 cinematic 子集</div></div>
<div class="row-label row-b-label">最优方向 / 改构图 / 大改 · 含实际轮次与 Absolute-5D</div>
<div class="five-col-grid">''')
        smap = by_slug.get(slug) or {}
        for scale in SCALE_ORDER:
            rec = smap.get(scale)
            badge, pcls, kind = SCALE_BADGE[scale]
            if not rec:
                parts.append(f'<div class="col-card"><span class="pmode-tag {pcls}">{badge}</span><div class="col-desc">缺失</div></div>')
                continue
            sc = rec["score"]
            rinfo = rounds_map.get(rec["bot_id"] or "") or {"label": "轮次N/A"}
            src = src_for(rec["path"], rec["filename"])
            r1_src = r1_total = r1_fn = None
            stem = rec["filename"].rsplit(".", 1)[0]
            r1_path = img_dir / f"{stem}_r1.jpg"
            if r1_path.is_file():
                r1_fn = r1_path.name
                r1_src = src_for(r1_path, r1_fn)
                r1_sc = scores.get(r1_fn) or {}
                r1_total = r1_sc.get("total")
            parts.append(card_html(
                badge=f"{rec['bot_id']} · {badge}",
                pmode_cls=pcls,
                src=src,
                filename=rec["filename"],
                total=sc.get("total"),
                grade=sc.get("grade") or "",
                dims=sc.get("dims") or {},
                defects=sc.get("defects") or [],
                rounds_label=rinfo.get("label") or "轮次N/A",
                kind=kind,
                r1_src=r1_src,
                r1_total=r1_total,
                r1_filename=r1_fn,
            ))
        parts.append("</div></section>")

    # Summary table
    parts.append('<section class="summary-block"><h2>分数汇总</h2><table class="accept-table"><tr><th>Bot</th><th>档</th><th>总分</th><th>等级</th><th>轮次</th><th>五维</th></tr>')
    for slug in ("night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"):
        for scale in SCALE_ORDER:
            rec = (by_slug.get(slug) or {}).get(scale)
            if not rec:
                continue
            sc = rec["score"]
            dims = sc.get("dims") or {}
            dim_txt = "/".join(str(dims.get(d, "—")) for d in DIMS)
            rinfo = rounds_map.get(rec["bot_id"] or "") or {}
            total = sc.get("total")
            parts.append(
                f"<tr><td><code>{rec['bot_id']}</code></td><td>{scale}</td>"
                f"<td><b>{total if total is not None else '—'}</b></td>"
                f"<td>{sc.get('grade') or ''}</td><td>{rinfo.get('label','')}</td><td>{dim_txt}</td></tr>"
            )
    parts.append("</table>")
    parts.append(
        f'<div class="qp-box"><b>对照说明</b><ul>'
        f"<li>前次 V8-20 均值 <b>{args.prev_mean}</b>（do_r2=false，单轮）；本批 V8→V2 调整 + 真 R2。</li>"
        f"<li>本批均值 <b>{v_mean}</b>，Δ = <b>{delta}</b>。</li>"
        f"<li>原图基线均值 <b>{base_mean}</b>（同尺）。</li>"
        f"<li>旧 V2 showcase 分为 scripted，不可与本批 Absolute-5D 横比。</li>"
        f"</ul></div></section>"
    )
    parts.append("</body></html>")
    out = Path(args.out)
    out.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {out} bots={len(bot_totals)} mean={v_mean} base_mean={base_mean} delta={delta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
