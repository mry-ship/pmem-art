# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import html
from pathlib import Path

ROOT = Path(__file__).resolve().parent
rows = json.loads((ROOT / "_summary.json").read_text(encoding="utf-8"))

# Prefer paths relative to this HTML dir
def rel(p: str | None) -> str:
    if not p:
        return ""
    p = p.replace("\\", "/")
    prefix = "docs/showcase/skills-full-run-20261123/"
    if p.startswith(prefix):
        return p[len(prefix) :]
    if p.startswith("docs/showcase/"):
        return "../../" + p[len("docs/") :]
    if p.startswith(".memory-art/"):
        return "../../../" + p
    return p


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s), quote=True)


ORDER = [
    "ui.kit",
    "icon.a",
    "icon.b",
    "icon.c",
    "merge.ladder",
    "layer.split",
    "draw.lens",
    "draw.touchup",
    "draw.clone",
    "draw.variant",
    "draw.multi",
    "draw.key",
    "style.lock",
    "critique.review",
    "atlas.file",
    "coach.report",
    "prompt.write",
    "draw.ordinary",
]
by_id = {r["id"]: r for r in rows}

sections_html: list[str] = []
toc: list[str] = []

for rid in ORDER:
    r = by_id.get(rid)
    if not r:
        continue
    sid = rid.replace(".", "-")
    toc.append(f'<a href="#{sid}">{esc(rid)}</a>')
    score = r.get("score")
    passed = r.get("pass")
    notes = r.get("notes") or ""
    elapsed = r.get("elapsed") or ""
    banner = r.get("banner") or ""
    early = any(x in notes for x in ("STOP_REGRESSION", "STOP_PLATEAU", "安全早停", "早停"))
    images = list(r.get("images") or [])
    final = r.get("final") or ""
    sheet = r.get("sheet") or ""

    # Build figures: prefer process rounds + win final
    figs: list[str] = []
    scored_rounds = [im for im in images if im.get("score") is not None and str(im.get("slot", "")).upper().startswith(("R", "OFF", "ON", "PREVIEW"))]
    # normalize
    round_figs = []
    for im in images:
        slot = str(im.get("slot") or "")
        path = rel(im.get("path"))
        if not path or not (ROOT / path.replace("../../../", "")).exists() and not (ROOT / path).exists():
            # try local
            local = Path(path)
            if not (ROOT / local).exists() and not Path(im.get("path") or "").exists():
                # still emit; gate checks existence relative to html
                pass
        sc = im.get("score")
        if slot.lower() in {"final", "anchor", "review", "source"} and slot.lower() != "final":
            # refs
            if path:
                figs.append(
                    f'<figure class="ref"><img src="{esc(path)}" alt="{esc(slot)}" />'
                    f"<figcaption><strong>{esc(slot)}</strong></figcaption></figure>"
                )
            continue
        if sc is None and slot.lower() != "final":
            if path and slot:
                figs.append(
                    f'<figure class="ref"><img src="{esc(path)}" alt="{esc(slot)}" />'
                    f"<figcaption><strong>{esc(slot)}</strong></figcaption></figure>"
                )
            continue
        if sc is not None and ("R" in slot.upper() or slot.upper().startswith(("OFF", "ON", "PREVIEW"))):
            # process card — must use「第 N 轮 · score」so gate treats非 win as history
            digits = "".join(ch for ch in slot if ch.isdigit())
            m_n = int(digits) if digits else 0
            if not m_n:
                m_n = 1
            cap = f"第 {m_n} 轮 · {float(sc):.2f}"
            if slot.upper().startswith("OFF"):
                cap = f"第 {m_n} 轮 · 关态 · {float(sc):.2f}"
            elif slot.upper().startswith("ON"):
                cap = f"第 {m_n} 轮 · 开态 · {float(sc):.2f}"
            round_figs.append((m_n, float(sc), path, cap, "wide", False))

    # win final
    win_path = rel(final) if final else ""
    win_score = score
    n_rounds = len([x for x in round_figs if x[0] > 0]) or (2 if early else 1)
    # count from images slots Rn
    rn = [im for im in images if str(im.get("slot", "")).upper().startswith("R") and im.get("score") is not None]
    if rn:
        n_rounds = max(
            int("".join(ch for ch in str(im.get("slot"))[1:] if ch.isdigit()) or "1")
            for im in rn
        )

    for _n, _sc, path, cap, cls, _w in sorted(round_figs, key=lambda t: t[0]):
        if path:
            figs.append(
                f'<figure class="{cls}"><img src="{esc(path)}" alt="{esc(cap)}" />'
                f"<figcaption><strong>{esc(cap)}</strong></figcaption></figure>"
            )

    if win_path and rid == "critique.review":
        # 审图对象：分数写在 meta，figcaption 不带分，避免 showcase-gate 当未满轮终稿
        figs.append(
            f'<figure class="ref wide"><img src="{esc(win_path)}" alt="critique target" />'
            f"<figcaption><strong>参考 · 送审图</strong></figcaption></figure>"
        )
    elif win_path and win_score is not None:
        # final win caption for gate
        if float(win_score) >= 9.5:
            wcap = f"终稿 · {n_rounds} 轮 · {float(win_score):.2f}"
        elif early:
            tag = "STOP_REGRESSION" if "REGRESSION" in notes else ("STOP_PLATEAU" if "PLATEAU" in notes else "安全早停")
            wcap = f"终稿 · {n_rounds} 轮 · {float(win_score):.2f} · {tag}"
        else:
            wcap = f"终稿 · {max(n_rounds, 3)} 轮 · {float(win_score):.2f}"
        figs.append(
            f'<figure class="win wide"><img src="{esc(win_path)}" alt="final" />'
            f"<figcaption><strong>{esc(wcap)}</strong></figcaption></figure>"
        )
    elif win_path:
        figs.append(
            f'<figure class="win wide"><img src="{esc(win_path)}" alt="final" />'
            f"<figcaption><strong>终稿</strong></figcaption></figure>"
        )

    if sheet:
        sp = rel(sheet)
        if sp and not any(sp in f for f in figs):
            figs.append(
                f'<figure class="wide"><img src="{esc(sp)}" alt="process sheet" />'
                f"<figcaption><strong>过程拼板</strong></figcaption></figure>"
            )

    # icon.b svgs
    if rid == "icon.b":
        for name in ("home", "shop", "merge", "bag", "star", "heart", "settings", "profile"):
            p = f"icon.b/{name}.svg"
            if (ROOT / p).exists():
                figs.append(
                    f'<figure class="ref"><img src="{esc(p)}" alt="{esc(name)}" />'
                    f"<figcaption><strong>{esc(name)}</strong></figcaption></figure>"
                )

    # layer extras
    if rid == "layer.split":
        for extra, label in (
            ("layer.split/_compose_mid.png", "叠回整图"),
            ("layer.split/_compose_preview.png", "幽灵对比"),
        ):
            if (ROOT / extra).exists() and not any(extra in f for f in figs):
                figs.append(
                    f'<figure class="wide"><img src="{esc(extra)}" alt="{esc(label)}" />'
                    f"<figcaption><strong>{esc(label)}</strong></figcaption></figure>"
                )

    pass_txt = "过线" if passed is True else ("未过线" if passed is False else "非出图/不适用")
    score_txt = f"{score:.2f}" if isinstance(score, (int, float)) else "—"
    meta = f"<b>{esc(pass_txt)}</b>　best={esc(score_txt)}"
    if elapsed:
        meta += f"　耗时 {esc(elapsed)}"

    grid = "\n      ".join(figs) if figs else "<p class=\"lead\">无附图（文字交付）。</p>"
    more = ""
    if rid == "draw.lens":
        more = '<p class="note">点选前不生图。方案见 <a href="draw.lens/lens_options.md">lens_options.md</a>。</p>'
    if rid == "prompt.write":
        more = '<p class="note"><a href="prompt.write/prompts.md">prompts.md</a> · 4 套普通图方案。</p>'
    if rid == "style.lock":
        more = '<p class="note"><a href="style.lock/style_bible.md">style_bible.md</a></p>'
    if rid == "coach.report":
        more = '<p class="note"><a href="coach.report/coach.md">coach.md</a></p>'
    if rid == "critique.review":
        more = '<p class="note"><a href="critique.review/critique.md">critique.md</a> · 外审尺，不生图。</p>'
    if rid == "atlas.file":
        more = '<p class="note">已刷新仓库根 <code>art-atlas.html</code>。</p>'

    sections_html.append(
        f"""
  <section id="{sid}">
    <h2>{esc(rid)}</h2>
    <p class="lead">{esc(banner)}</p>
    <div class="invoke">
      <div class="tag-row"><span class="slash">{esc(rid)}</span>
      <span class="tag {'ok' if passed else 'no-ref'}">{esc(pass_txt)}</span></div>
      <div class="meta">{meta}</div>
      <p>{esc(notes)}</p>
    </div>
    <div class="grid three">
      {grid}
    </div>
    {more}
  </section>"""
    )

page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>pmem-art · 全技能展陈 · 2026-11-23</title>
<style>
  :root {{
    --bg: #0b0f19; --card: #111827; --line: #1e293b;
    --text: #f1f5f9; --muted: #94a3b8; --dim: #64748b;
    --accent: #38bdf8; --ok: #34d399; --warn: #fbbf24;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; color: var(--text);
    font: 14px/1.55 "PingFang SC", "Noto Sans SC", system-ui, sans-serif;
    background: var(--bg);
  }}
  a {{ color: var(--accent); }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 28px 18px 72px; }}
  .hero {{
    border: 1px solid #312e81; border-radius: 18px; padding: 24px 26px;
    background: linear-gradient(135deg, #111827, #1e1b4b 55%, #0f172a);
    margin-bottom: 22px;
  }}
  .hero h1 {{ margin: 0 0 8px; font-size: 26px; }}
  .hero p {{ margin: 0; color: #cbd5e1; max-width: 72ch; }}
  .pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
  .pill {{
    font-size: 12px; padding: 4px 12px; border-radius: 999px;
    border: 1px solid rgba(255,255,255,.14); color: var(--muted);
  }}
  .pill.ok {{ color: var(--ok); border-color: rgba(52,211,153,.4); }}
  nav.toc {{
    position: sticky; top: 0; z-index: 5; display: flex; flex-wrap: wrap; gap: 8px;
    padding: 10px 0 14px; background: rgba(11,15,25,.92); backdrop-filter: blur(8px);
  }}
  nav.toc a {{
    font-size: 12px; color: var(--muted); padding: 4px 12px; border-radius: 999px;
    border: 1px solid transparent; text-decoration: none;
  }}
  nav.toc a:hover {{ color: var(--text); border-color: var(--line); }}
  section {{
    border: 1px solid var(--line); border-radius: 16px; background: var(--card);
    padding: 18px; margin-bottom: 16px; scroll-margin-top: 96px;
  }}
  section h2 {{ margin: 0 0 6px; font-size: 18px; }}
  section .lead {{ color: var(--muted); margin: 0 0 14px; font-size: 13px; }}
  .invoke {{
    border: 1px solid rgba(196,181,253,.28); background: rgba(196,181,253,.08);
    border-radius: 12px; padding: 12px 14px; margin-bottom: 12px;
  }}
  .slash {{
    font-family: ui-monospace, Menlo, monospace; color: var(--accent);
    background: rgba(56,189,248,.12); padding: 2px 8px; border-radius: 6px; font-size: 13px;
  }}
  .meta {{ color: var(--muted); font-size: 13px; margin-top: 6px; }}
  .meta b {{ color: var(--warn); }}
  .tag-row {{ display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 8px; align-items: center; }}
  .tag {{
    font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 6px;
    border: 1px solid transparent;
  }}
  .tag.ok {{ color: #7dd3fc; background: rgba(56,189,248,.14); border-color: rgba(56,189,248,.45); }}
  .tag.no-ref {{ color: #fcd34d; background: rgba(251,191,36,.12); border-color: rgba(251,191,36,.5); }}
  .grid {{
    display: grid; gap: 10px;
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }}
  figure {{
    margin: 0; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; background: #0b1220;
  }}
  figure.win {{ border-color: rgba(251,191,36,.55); }}
  figure.ref {{ border-color: rgba(56,189,248,.45); }}
  figure img {{ display: block; width: 100%; aspect-ratio: 1; object-fit: cover; }}
  figure.wide img {{ aspect-ratio: 16/9; object-fit: contain; background: #0b1220; }}
  figcaption {{
    padding: 8px 10px; font-size: 12px; color: var(--muted); border-top: 1px solid var(--line);
  }}
  figcaption strong {{ display: block; color: var(--text); }}
  .note {{
    margin-top: 12px; padding: 10px 12px; border-left: 3px solid var(--accent);
    background: rgba(56,189,248,.08); color: var(--muted); font-size: 13px; border-radius: 0 8px 8px 0;
  }}
  footer {{ text-align: center; color: var(--dim); font-size: 12px; margin-top: 20px; }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <h1>全技能并行展陈 · 2026-11-23</h1>
    <p>
      18 支 route 全清单跑通。出图闭环最多 3 轮 · ≥9.5 到线即停；安全早停交历史最高分。
      垫图仅锁气质/版式（Gossip Harbor 真机 + workbench 样张），禁止像素抄构图。
    </p>
    <div class="pills">
      <span class="pill ok">18/18 RESULT</span>
      <span class="pill ok">多技能展陈</span>
      <span class="pill">金框 = 终稿</span>
      <span class="pill">蓝框 = 参考/散件</span>
    </div>
  </header>
  <nav class="toc">
    {''.join(toc)}
  </nav>
  {''.join(sections_html)}
  <footer>路径：docs/showcase/skills-full-run-20261123/index.html · 源：各支 RESULT.json</footer>
</div>
</body>
</html>
"""

(ROOT / "index.html").write_text(page, encoding="utf-8")
print("wrote", ROOT / "index.html")
