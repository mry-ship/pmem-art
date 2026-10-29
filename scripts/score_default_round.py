#!/usr/bin/env python3
"""Blind 0-10 scores for the default-generator round. Image only, no rubric."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "docs" / "showcase" / "default_round"
IMG = BOARD / "images"
THUMBS = BOARD / "_thumbs"
GPT = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\gpt.py")
OUT = BOARD / "plain_scores.json"

CASE_ORDER = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
SCALE_ORDER = ["ref", "low", "medium", "high", "recompose"]
CASE_CN = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}
LABEL = {
    "ref": "原图",
    "low": "low",
    "medium": "medium",
    "high": "high",
    "recompose": "recompose",
}
PROMPT = """只看这张图。按你自己的判断给一个 0 到 10 的总分，保留一位小数。10 是你愿意当作成品收下来的图。
不要使用任何固定维度、检查清单或加权公式。
只输出一个 JSON，不要 markdown：
{"score":0.0,"reason":"一句话说明为什么是这个分"}
"""


def thumbs() -> None:
    from PIL import Image

    THUMBS.mkdir(parents=True, exist_ok=True)
    for path in sorted(IMG.iterdir()):
        if path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        dest = THUMBS / (path.stem + ".jpg")
        with Image.open(path) as im:
            im = im.convert("RGB")
            im.thumbnail((768, 768))
            im.save(dest, "JPEG", quality=82)


def parse_score(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    data = json.loads(text[start : end + 1])
    score = round(float(data["score"]), 1)
    if not 0 <= score <= 10:
        raise ValueError("score out of range")
    return {"score": score, "reason": str(data.get("reason") or "").strip()}


def call(model: str, img: Path) -> tuple[dict, str]:
    proc = subprocess.run(
        [sys.executable, str(GPT), "-m", model, "--effort", "medium", "--image", str(img), PROMPT],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=140,
    )
    used = model
    m = re.search(r"\[(\S+) 推理强度", proc.stderr or "")
    if m:
        used = m.group(1)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "failed")[:240])
    parsed = parse_score(proc.stdout or "")
    parsed["model"] = used
    return parsed, used


def files() -> list[Path]:
    out = []
    for slug in CASE_ORDER:
        out.append(IMG / f"{slug}_ref.png")
        for scale in ("low", "medium", "high", "recompose"):
            out.append(IMG / f"{slug}_{scale}.jpg")
    return out


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tone(score: float) -> str:
    if score >= 9.6:
        return "hit"
    if score >= 8.5:
        return "mid"
    return "low"


def render(scores: dict) -> None:
    totals = []
    sections = []
    for slug in CASE_ORDER:
        cards = []
        for scale in SCALE_ORDER:
            name = f"{slug}_{scale}.png" if scale == "ref" else f"{slug}_{scale}.jpg"
            row = scores.get(name) or {}
            score = row.get("score")
            if isinstance(score, (int, float)):
                totals.append(float(score))
                mark = f'<span class="total {tone(float(score))}">({score:.1f})</span>'
            else:
                mark = '<span class="total low">(—)</span>'
            reason = esc(row.get("reason") or row.get("error") or "")
            rnd = row.get("round")
            cap = LABEL[scale] if not rnd else f"{LABEL[scale]} · 第 {int(rnd)} 轮"
            extra = ""
            if row.get("mine") is not None and row.get("a5d") is not None:
                dims = esc(str(row.get("dims") or ""))
                extra = (
                    f'<p class="extra">我的分 {float(row["mine"]):.1f}'
                    f' · Absolute-5D {float(row["a5d"]):.2f}'
                    + (f' · {dims}' if dims else "")
                    + "</p>"
                )
            cards.append(
                f'<figure class="card {scale}">'
                f'<figcaption>{cap}</figcaption>'
                f'<div class="shot">{mark}<img src="images/{name}" alt="{cap}"></div>'
                f'{extra}'
                f'<p class="reason">{reason}</p></figure>'
            )
        sections.append(f"<section><h2>{CASE_CN[slug]}</h2><div class=\"row\">{''.join(cards)}</div></section>")
    hit = sum(1 for t in totals if t >= 9.6)
    mean = round(sum(totals) / len(totals), 2) if totals else 0
    model = next((v.get("model") for v in scores.values() if v.get("model")), "gpt")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>默认出图 · GPT 盲评</title>
<style>
  body {{ margin: 0; background: #141414; color: #eee; font-family: "Segoe UI", sans-serif; }}
  header {{ padding: 24px 28px 8px; }}
  h1 {{ font-size: 22px; font-weight: 600; margin: 0 0 8px; }}
  p.note {{ color: #aaa; max-width: 980px; line-height: 1.5; }}
  section {{ padding: 8px 20px 28px; }}
  h2 {{ font-size: 16px; margin: 12px 8px; }}
  .row {{ display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }}
  .card {{ margin: 0; background: #1e1e1e; border: 1px solid #333; padding: 8px; }}
  .card.ref {{ border-color: #6a5a3a; }}
  figcaption {{ font-size: 12px; margin-bottom: 6px; color: #ddd; }}
  .shot {{ position: relative; }}
  .total {{
    position: absolute; top: 8px; left: 8px; z-index: 1;
    font-variant-numeric: tabular-nums; font-weight: 650;
    background: rgba(0,0,0,.62); padding: 2px 7px; border-radius: 4px;
  }}
  .total.hit {{ color: #8fd18f; }}
  .total.mid {{ color: #e6c36a; }}
  .total.low {{ color: #e0a0a0; }}
  img {{ width: 100%; height: auto; display: block; background: #0e0e0e; }}
  .extra {{ margin: 6px 0 0; font-size: 11px; color: #c8c8c8; line-height: 1.35; }}
  .reason {{ margin-top: 4px; font-size: 12px; color: #ddd; line-height: 1.4; }}
</style>
</head>
<body>
<header>
  <h1>案例 01–04 · 默认出图 · GPT 盲评</h1>
  <p class="note">图上左上角括号里的数字是 {esc(model)} 盲评。图下第一行是我看图给的总分，以及按档位权重算出的 Absolute-5D（构图/光影/透视/质感/风格）。新图都是第 1 轮，没有第二轮。盲评 {hit}/{len(totals)} 张 ≥9.60，均分 {mean:.2f}。</p>
</header>
{''.join(sections)}
</body>
</html>
"""
    (BOARD / "index.html").write_text(html, encoding="utf-8")


def main() -> None:
    thumbs()
    scores: dict = {}
    if OUT.is_file():
        scores = json.loads(OUT.read_text(encoding="utf-8"))
    model = "gpt-6-astra"
    for path in files():
        key = path.name
        if scores.get(key, {}).get("score") is not None:
            print(f"SKIP {key} {scores[key]['score']}", flush=True)
            continue
        img = THUMBS / (path.stem + ".jpg")
        print(f"SCORE {key} via {model}", flush=True)
        try:
            parsed, used = call(model, img)
        except Exception as e:
            err = str(e)[:200]
            print(f"  fail {model}: {err}", flush=True)
            if model == "gpt-6-astra":
                model = "gpt-5.6-terra"
                print(f"  switch {model}", flush=True)
                try:
                    parsed, used = call(model, img)
                except Exception as e2:
                    scores[key] = {"score": None, "reason": "", "error": str(e2)[:200], "model": model}
                    OUT.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
                    continue
            else:
                scores[key] = {"score": None, "reason": "", "error": err, "model": model}
                OUT.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
                continue
        model = "gpt-5.6-terra" if "terra" in used else model
        scores[key] = parsed
        print(f"OK {key} {parsed['score']} {used}", flush=True)
        OUT.write_text(json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8")
        render(scores)
    render(scores)
    print("DONE", flush=True)


if __name__ == "__main__":
    main()
