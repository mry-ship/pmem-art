# -*- coding: utf-8 -*-
"""Collect suite RESULT.json files and emit ANALYSIS.md + showcase.html."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "out"
ORDER = [
    "ui.kit",
    "icon.a",
    "icon.b",
    "icon.c",
    "merge.ladder",
    "draw.lens",
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


def load_results() -> list[dict]:
    rows: list[dict] = []
    for rid in ORDER:
        p = OUT / rid / "RESULT.json"
        if not p.exists():
            rows.append({"route_id": rid, "status": "missing", "passed_line": False})
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            rows.append({"route_id": rid, "status": f"bad_json:{exc}", "passed_line": False})
            continue
        data.setdefault("route_id", rid)
        rows.append(data)
    return rows


def write_analysis(rows: list[dict]) -> Path:
    lines = [
        f"# 全技能清点分析 · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 总览",
        "",
        f"- 已交卷：{sum(1 for r in rows if r.get('status') != 'missing')}/{len(rows)}",
        f"- 过线(≥9.5)：{sum(1 for r in rows if r.get('passed_line') is True)}",
        f"- 文字交付：{sum(1 for r in rows if r.get('status') == 'text_only')}",
        f"- 缺失：{sum(1 for r in rows if r.get('status') == 'missing')}",
        "",
        "## 分技能",
        "",
        "| route | status | rounds | best | passed | final | notes |",
        "| :--- | :--- | ---: | ---: | :---: | :--- | :--- |",
    ]
    for r in rows:
        scores = r.get("scores") or []
        best = max((s.get("total") or 0) for s in scores) if scores else ""
        lines.append(
            "| {rid} | {st} | {rnd} | {best} | {pl} | {fin} | {notes} |".format(
                rid=r.get("route_id"),
                st=r.get("status"),
                rnd=r.get("rounds", ""),
                best=best,
                pl="Y" if r.get("passed_line") else ("—" if r.get("status") == "text_only" else "N"),
                fin=(r.get("final_image") or r.get("text_deliverable") or ""),
                notes=(r.get("notes") or "").replace("|", "/"),
            )
        )
    lines += [
        "",
        "## 交叉观察（自动占位，父级可改）",
        "",
        "1. 垫图对位是否生效：UI/AppIcon/Merge 是否各自跟对类型参考。",
        "2. 合同是否串味：普通图有没有误升 UI/合成梯；克隆有没有贴样张构图。",
        "3. 并发副作用：session 是否撞车、是否误用 latest。",
        "4. 商业对标：merge 是否跟 GH 货面；非 merge 是否误套货柜。",
        "",
    ]
    path = ROOT / "ANALYSIS.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_showcase(rows: list[dict]) -> Path:
    cards = []
    for r in rows:
        img = r.get("final_image") or ""
        rel = ""
        if img:
            try:
                rel = Path(img).as_posix()
                if "skill_20261112_suite/" in rel:
                    rel = rel.split("skill_20261112_suite/", 1)[1]
                elif rel.startswith("assets/"):
                    rel = rel
            except Exception:
                rel = img
        media = (
            f'<img src="{rel}" alt="{r.get("route_id")}"/>'
            if img and Path(ROOT / rel.replace("out/", "out/")).exists() or img
            else f'<pre>{(r.get("text_deliverable") or r.get("notes") or r.get("status") or "")}</pre>'
        )
        # Prefer relative from showcase.html location
        if img:
            p = Path(img)
            if not p.is_absolute():
                p = Path.cwd() / p
            try:
                media = f'<img src="{Path(img).as_posix().split("skill_20261112_suite/")[-1]}" alt="{r.get("route_id")}"/>'
            except Exception:
                pass
        scores = r.get("scores") or []
        best = max((s.get("total") or 0) for s in scores) if scores else "—"
        cards.append(
            f"""<article class="card">
  <h2>{r.get("route_id")}</h2>
  <p class="meta">{r.get("status")} · best={best} · passed={r.get("passed_line")}</p>
  <div class="media">{media}</div>
  <p class="notes">{(r.get("notes") or "")}</p>
</article>"""
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<title>pmem-art 全技能清点 2026-11-12</title>
<style>
body{{font-family:Segoe UI,system-ui,sans-serif;margin:24px;background:#111;color:#eee}}
h1{{font-size:1.4rem}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}}
.card{{background:#1b1b1b;border:1px solid #333;border-radius:12px;padding:12px}}
.card img{{width:100%;height:auto;border-radius:8px;background:#000}}
.meta{{opacity:.7;font-size:.85rem}}
pre{{white-space:pre-wrap;font-size:.8rem;background:#0d0d0d;padding:8px;border-radius:8px}}
</style>
</head>
<body>
<h1>全技能清点展陈 · Brimwave Café × Gossip Harbor 对位垫图</h1>
<p>生成时间 {datetime.now().isoformat(timespec="minutes")}</p>
<div class="grid">
{''.join(cards)}
</div>
</body>
</html>
"""
    path = ROOT / "showcase.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> None:
    rows = load_results()
    a = write_analysis(rows)
    s = write_showcase(rows)
    print(json.dumps({"analysis": str(a), "showcase": str(s), "n": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
