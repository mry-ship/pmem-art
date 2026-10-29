#!/usr/bin/env python3
"""Plain vision score for the rerun board. No Absolute-5D checklist or weights."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "docs" / "showcase" / "rerun_5scale"
GPT = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\gpt.py")
THUMBS = BOARD / "_thumbs"
WORKERS = 4
CASE_ORDER = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
CASE_CN = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}

PROMPT = """只看这张图。按你自己的判断给一个 0 到 10 的总分，保留一位小数。10 是你愿意当作成品收下来的图。
不要使用任何固定维度、检查清单或加权公式。
只输出一个 JSON，不要 markdown：
{"score":0.0,"reason":"一句话说明为什么是这个分"}
"""


def parse_score(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    data = json.loads(text[start : end + 1])
    score = round(float(data["score"]), 1)
    if not 0 <= score <= 10:
        raise ValueError("score out of range")
    return {"score": score, "reason": str(data.get("reason") or "").strip(), "ok": True}


def score_file(path: Path) -> dict:
    img = THUMBS / (path.stem + ".jpg")
    if not img.is_file():
        img = path
    print(f"PLAIN {path.name}", flush=True)
    last = ""
    for attempt in range(1, 3):
        proc = subprocess.run(
            [sys.executable, str(GPT), "--effort", "medium", "--image", str(img), PROMPT],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=700,
        )
        model = "gpt-6-astra"
        m = re.search(r"\[(\S+) 推理强度", proc.stderr or "")
        if m:
            model = m.group(1)
        if proc.returncode != 0:
            last = (proc.stderr or proc.stdout or "failed")[:240]
            print(f"  retry {attempt} {path.name}: {last[:120]}", flush=True)
            continue
        try:
            parsed = parse_score(proc.stdout or "")
        except Exception as e:
            last = f"{type(e).__name__}: {(proc.stdout or '')[:160]}"
            print(f"  retry {attempt} {path.name}: {last[:120]}", flush=True)
            continue
        parsed["model"] = model
        print(f"OK {path.name} {parsed['score']}", flush=True)
        return parsed
    return {"ok": False, "error": last, "score": None, "reason": "", "model": ""}


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tone(score: float) -> str:
    if score >= 9.5:
        return "hit"
    if score >= 8.5:
        return "mid"
    return "low"


def render(rows: list[dict], plain: dict, five: dict) -> None:
    sys.path.insert(0, str(REPO / "scripts"))
    import score_rerun_5scale as five_mod

    by_case: dict[str, list[dict]] = {}
    for row in rows:
        by_case.setdefault(row["slug"], []).append(row)
    sections = []
    plain_totals = []
    for slug in CASE_ORDER:
        items = sorted(by_case.get(slug) or [], key=lambda r: SCALE_ORDER.index(r["display_scale"]))
        ref_file = next((p.name for p in (BOARD / "images").glob(slug + "_ref.*")), "")
        cards = [card(slug, "原图", ref_file, plain.get(ref_file) or {}, five.get(ref_file) or {}, "ref")]
        if (plain.get(ref_file) or {}).get("ok"):
            plain_totals.append(float(plain[ref_file]["score"]))
        for it in items:
            name = Path(it["file"]).name
            cards.append(card(slug, it["label"], name, plain.get(name) or {}, five.get(name) or {}, it["display_scale"], it.get("prompt") or ""))
            if (plain.get(name) or {}).get("ok"):
                plain_totals.append(float(plain[name]["score"]))
        sections.append(f"<section><h2>{CASE_CN[slug]}</h2><div class=\"row\">{''.join(cards)}</div></section>")
    hit = sum(1 for t in plain_totals if t >= 9.5)
    mean = round(sum(plain_totals) / len(plain_totals), 2) if plain_totals else None
    note = (
        "大标题上的分数是 gpt-6-astra 直接看图给的总分，推理强度 medium，没有五维检查表，也没有档位加权。"
        f" 直评 {hit}/{len(plain_totals)} 张 ≥9.50"
        + (f"，均分 {mean:.2f}。" if mean is not None else "。")
        + " 图下灰色小字仍是上一轮 Absolute-5D 加权分，方便对照。"
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>案例 01–04 · 直评对照</title>
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
  .reason {{ margin-top: 6px; font-size: 12px; color: #ddd; line-height: 1.4; }}
  .dims {{ margin-top: 4px; font-size: 11px; color: #8d8d8d; }}
  details {{ margin-top: 6px; font-size: 11px; color: #9a9a9a; }}
  details p {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<header>
  <h1>案例 01–04 · 大模型直评</h1>
  <p class="note">{esc(note)}</p>
</header>
{''.join(sections)}
</body>
</html>
"""
    (BOARD / "index.html").write_text(html, encoding="utf-8")
    del five_mod


def card(slug: str, label: str, filename: str, plain: dict, five: dict, scale: str, prompt: str = "") -> str:
    ref_cls = " ref" if scale == "ref" else ""
    if not plain.get("ok"):
        err = esc(plain.get("error") or "未评分")
        return f'<figure class="card{ref_cls}"><figcaption><span>{esc(label)}</span></figcaption><img src="images/{esc(filename)}" alt=""><p class="reason">{err}</p></figure>'
    score = float(plain["score"])
    five_bit = ""
    if five.get("ok") and five.get("dims"):
        sys.path.insert(0, str(REPO / "scripts"))
        import score_rerun_5scale as five_mod
        total, kind = five_mod.weighted(five["dims"], scale)
        five_bit = f'<div class="dims">Absolute-5D {kind} {total:.2f}</div>'
    extra = f"<details><summary>本档提示词</summary><p>{esc(prompt)}</p></details>" if prompt else ""
    return f"""<figure class="card{ref_cls}">
  <figcaption><span>{esc(label)}</span><span class="total {tone(score)}">{score:.1f}</span></figcaption>
  <img src="images/{esc(filename)}" alt="{esc(CASE_CN.get(slug, slug) + ' ' + label)}">
  <div class="reason">{esc(plain.get('reason') or '')}</div>
  {five_bit}
  {extra}
</figure>"""


def targets() -> list[Path]:
    rows = json.loads((BOARD / "manifest.json").read_text(encoding="utf-8"))
    found: list[Path] = []
    for slug in CASE_ORDER:
        found.extend(sorted((BOARD / "images").glob(slug + "_ref.*")))
    for row in rows:
        if row.get("ok") and row.get("file"):
            found.append(BOARD / row["file"])
    seen = []
    for p in found:
        if p.is_file() and p not in seen:
            seen.append(p)
    return seen


def main() -> int:
    rows = json.loads((BOARD / "manifest.json").read_text(encoding="utf-8"))
    five = json.loads((BOARD / "scores.json").read_text(encoding="utf-8"))
    path = BOARD / "plain_scores.json"
    done = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    pending = [p for p in targets() if not (done.get(p.name) or {}).get("ok")]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(score_file, p): p for p in pending}
        for fut in as_completed(futs):
            p = futs[fut]
            try:
                done[p.name] = fut.result()
            except Exception as e:
                done[p.name] = {"ok": False, "error": str(e)[:240], "score": None, "reason": ""}
            path.write_text(json.dumps(done, ensure_ascii=False, indent=2), encoding="utf-8")
    render(rows, done, five)
    ok = sum(1 for p in targets() if (done.get(p.name) or {}).get("ok"))
    print(f"DONE {ok}/{len(targets())} -> {BOARD / 'index.html'}")
    return 0 if ok == len(targets()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
