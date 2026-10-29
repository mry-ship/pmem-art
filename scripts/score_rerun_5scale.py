#!/usr/bin/env python3
"""Score the homepage rerun board with Absolute-5D and rewrite index.html."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "docs" / "showcase" / "rerun_5scale"
GPT = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\gpt.py")
THUMBS = BOARD / "_thumbs"
WORKERS = 4

DIMS = (
    "composition",
    "lighting_color",
    "perspective_anatomy",
    "texture_detail",
    "spec_style",
)
DIM_CN = {
    "composition": "构图",
    "lighting_color": "光影",
    "perspective_anatomy": "透视",
    "texture_detail": "质感",
    "spec_style": "风格",
}
WEIGHTS = {
    "low_best": {
        "composition": 0.15,
        "lighting_color": 0.20,
        "perspective_anatomy": 0.25,
        "texture_detail": 0.25,
        "spec_style": 0.15,
    },
    "medium_best": {
        "composition": 0.20,
        "lighting_color": 0.25,
        "perspective_anatomy": 0.20,
        "texture_detail": 0.20,
        "spec_style": 0.15,
    },
    "high_best": {
        "composition": 0.15,
        "lighting_color": 0.30,
        "perspective_anatomy": 0.15,
        "texture_detail": 0.20,
        "spec_style": 0.20,
    },
    "recompose": {
        "composition": 0.30,
        "lighting_color": 0.20,
        "perspective_anatomy": 0.20,
        "texture_detail": 0.15,
        "spec_style": 0.15,
    },
}
EQUAL = {k: 0.2 for k in DIMS}
CASE_ORDER = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
CASE_CN = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}

PROMPT = """你是独立主美裁判。只看这张图，按 Absolute-5D 打分，不要因为文件名猜测档位。
档位锚：3=失败 / 5=差 / 7=合格 / 8.5=近优 / 9.5=优（可到 10）。
五维各 0–10，保留一位小数：构图、光影色彩、透视与解剖、质感、规格与风格。
有结构、透视、手部、糊边、风格跑偏就必须压到 9 以下。缺陷必须是画面里能指出来的问题，禁止写「无明显硬伤」。
只输出一个 JSON 对象，不要 markdown：
{"composition":0,"lighting_color":0,"perspective_anatomy":0,"texture_detail":0,"spec_style":0,"defects":["具体问题"],"strengths":["具体优点"]}
"""


def thumb(src: Path) -> Path:
    THUMBS.mkdir(parents=True, exist_ok=True)
    dst = THUMBS / (src.stem + ".jpg")
    if dst.is_file() and dst.stat().st_mtime >= src.stat().st_mtime:
        return dst
    im = Image.open(src).convert("RGB")
    im.thumbnail((1024, 1024))
    im.save(dst, "JPEG", quality=85)
    return dst


def parse_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    data = json.loads(text[start : end + 1])
    dims = {}
    for k in DIMS:
        dims[k] = round(float(data[k]), 1)
        if not 0 <= dims[k] <= 10:
            raise ValueError(f"{k} out of range")
    defects = data.get("defects") or []
    strengths = data.get("strengths") or []
    if isinstance(defects, str):
        defects = [defects]
    if isinstance(strengths, str):
        strengths = [strengths]
    return {"dims": dims, "defects": [str(x) for x in defects][:3], "strengths": [str(x) for x in strengths][:2]}


def score_file(path: Path) -> dict:
    img = thumb(path)
    print(f"SCORE {path.name}", flush=True)
    last = ""
    for attempt in range(1, 3):
        proc = subprocess.run(
            [sys.executable, str(GPT), "--effort", "medium", "--image", str(img), PROMPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        blob = (proc.stdout or "") + "\n" + (proc.stderr or "")
        model = "gpt-6-astra"
        m = re.search(r"\[(\S+) 推理强度", proc.stderr or "")
        if m:
            model = m.group(1)
        if proc.returncode != 0:
            last = (proc.stderr or proc.stdout or "score failed")[:240]
            print(f"  retry {attempt} {path.name}: {last[:120]}", flush=True)
            continue
        try:
            parsed = parse_json(proc.stdout or "")
        except Exception as e:
            last = f"{type(e).__name__}: {(proc.stdout or '')[:180]}"
            print(f"  retry {attempt} {path.name}: {last[:120]}", flush=True)
            continue
        parsed["model"] = model
        parsed["ok"] = True
        print(f"OK {path.name} {parsed['dims']}", flush=True)
        return parsed
    return {"ok": False, "error": last, "dims": {}, "defects": [], "strengths": [], "model": ""}


def weighted(dims: dict, scale: str) -> tuple[float, str]:
    w = WEIGHTS.get(scale, EQUAL)
    total = sum(float(dims[k]) * w[k] for k in DIMS)
    kind = "五维均分" if scale not in WEIGHTS else "档位加权"
    return round(total, 2), kind


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render(rows: list[dict], scores: dict[str, dict]) -> None:
    by_case: dict[str, list[dict]] = {}
    for row in rows:
        by_case.setdefault(row["slug"], []).append(row)
    sections = []
    totals = []
    for slug in CASE_ORDER:
        items = by_case.get(slug) or []
        items.sort(key=lambda r: SCALE_ORDER.index(r["display_scale"]))
        ref_name = Path(items[0]["ref"]).name if items else ""
        ref_file = next((p.name for p in (BOARD / "images").glob(slug + "_ref.*")), "")
        cards = [card_html("原图", ref_file, scores.get(ref_file, {}), "ref", slug)]
        if scores.get(ref_file, {}).get("ok"):
            t, _ = weighted(scores[ref_file]["dims"], "ref")
            totals.append(t)
        for it in items:
            name = Path(it["file"]).name if it.get("file") else ""
            cards.append(card_html(it["label"], name, scores.get(name, {}), it["display_scale"], slug, it.get("prompt") or ""))
            sc = scores.get(name) or {}
            if sc.get("ok"):
                t, _ = weighted(sc["dims"], it["display_scale"])
                totals.append(t)
        sections.append(f"<section><h2>{CASE_CN[slug]}</h2><div class=\"row\">{''.join(cards)}</div></section>")
    mean = round(sum(totals) / len(totals), 2) if totals else None
    reached = sum(1 for t in totals if t >= 9.5)
    note = (
        f"出图模型 gpt-image-2.5-sunburst，每格 1 轮。评分模型 gpt-6-astra（失败时脚本会改用兜底），推理强度 medium。"
        f" low / medium / high / recompose 的总分是档位权重合成；原图和大改是五维均分。合格线仍是 9.50。"
        f" 本页 {reached}/{len(totals)} 张 ≥9.50"
        + (f"，均分 {mean:.2f}。" if mean is not None else "。")
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>案例 01–04 · 五档重出</title>
<style>
  body {{ margin: 0; background: #141414; color: #eee; font-family: "Segoe UI", sans-serif; }}
  header {{ padding: 24px 28px 8px; }}
  h1 {{ font-size: 22px; font-weight: 600; margin: 0 0 8px; }}
  p.note {{ color: #aaa; max-width: 980px; line-height: 1.5; }}
  section {{ padding: 8px 20px 28px; }}
  h2 {{ font-size: 16px; margin: 12px 8px; }}
  .row {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }}
  .card {{ margin: 0; background: #1e1e1e; border: 1px solid #333; padding: 8px; }}
  .card.ref {{ border-color: #6a5a3a; }}
  figcaption {{ font-size: 12px; margin-bottom: 6px; color: #ddd; display: flex; justify-content: space-between; gap: 8px; }}
  .total {{ font-variant-numeric: tabular-nums; font-weight: 650; }}
  .total.hit {{ color: #8fd18f; }}
  .total.mid {{ color: #e6c36a; }}
  .total.low {{ color: #e0a0a0; }}
  img {{ width: 100%; height: auto; display: block; background: #0e0e0e; }}
  .dims {{ margin-top: 6px; font-size: 11px; color: #c8c8c8; line-height: 1.45; }}
  .defect {{ margin-top: 4px; font-size: 11px; color: #c98b8b; line-height: 1.4; }}
  details {{ margin-top: 6px; font-size: 11px; color: #9a9a9a; }}
  details p {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<header>
  <h1>案例 01–04 原图 × 五档重出</h1>
  <p class="note">{esc(note)}</p>
</header>
{''.join(sections)}
</body>
</html>
"""
    (BOARD / "index.html").write_text(html, encoding="utf-8")


def card_html(label: str, filename: str, sc: dict, scale: str, slug: str, prompt: str = "") -> str:
    ref_cls = " ref" if scale == "ref" else ""
    if not filename or not sc.get("ok"):
        err = esc(sc.get("error") or "未评分")
        return f'<figure class="card{ref_cls}"><figcaption><span>{esc(label)}</span></figcaption><img src="images/{esc(filename)}" alt="{esc(label)}"><p class="defect">{err}</p></figure>'
    total, kind = weighted(sc["dims"], scale)
    tone = "hit" if total >= 9.5 else "mid" if total >= 8.5 else "low"
    dims = " · ".join(f"{DIM_CN[k]} {sc['dims'][k]:.1f}" for k in DIMS)
    defect = esc("；".join(sc.get("defects") or [])[:140])
    extra = ""
    if prompt:
        extra = f"<details><summary>本档提示词</summary><p>{esc(prompt)}</p></details>"
    alt = CASE_CN.get(slug, slug) + " " + label
    return f"""<figure class="card{ref_cls}">
  <figcaption><span>{esc(label)}</span><span class="total {tone}">{total:.2f}</span></figcaption>
  <img src="images/{esc(filename)}" alt="{esc(alt)}">
  <div class="dims">{esc(kind)} · {esc(dims)}</div>
  <div class="defect">{defect}</div>
  {extra}
</figure>"""


def main() -> int:
    rows = json.loads((BOARD / "manifest.json").read_text(encoding="utf-8"))
    targets: list[Path] = []
    for slug in CASE_ORDER:
        targets.extend(sorted((BOARD / "images").glob(slug + "_ref.*")))
    for row in rows:
        if row.get("ok") and row.get("file"):
            targets.append(BOARD / row["file"])
    seen = []
    for p in targets:
        if p.is_file() and p not in seen:
            seen.append(p)
    scores_path = BOARD / "scores.json"
    done = {}
    if scores_path.is_file():
        done = json.loads(scores_path.read_text(encoding="utf-8"))
    pending = [p for p in seen if not (done.get(p.name) or {}).get("ok")]
    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(score_file, p): p for p in pending}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                results[p.name] = fut.result()
            except Exception as e:
                results[p.name] = {"ok": False, "error": str(e)[:240], "dims": {}, "defects": [], "strengths": []}
            done.update(results)
            scores_path.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    done.update({k: v for k, v in results.items()})
    # keep previously scored
    scores_path.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    render(rows, done)
    ok = sum(1 for p in seen if (done.get(p.name) or {}).get("ok"))
    print(f"DONE {ok}/{len(seen)} -> {BOARD / 'index.html'}")
    return 0 if ok == len(seen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
