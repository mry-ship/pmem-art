#!/usr/bin/env python3
"""Homepage cases 01-04 × five scales, one edit each, then a local HTML board.

Uses the same bot briefs and skills_kit scale contracts as the V8 showcase.
One round per cell so the board is viewable without an 8-round converge.
"""
from __future__ import annotations

import base64
import json
import mimetypes
import re
import shutil
import sys
import time
import urllib.error
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from skills_kit import (  # noqa: E402
    compose_style_first_prompt,
    get_converge_scale_profile,
    strip_affirmative_locks_from_prompt,
)

CFG = json.loads(
    Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-image\config.json").read_text(encoding="utf-8-sig")
)
OUT = REPO / "docs" / "showcase" / "rerun_5scale"
MODEL = "gpt-image-2.5-sunburst"
WANT = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
LABEL = {
    "low_best": "low",
    "medium_best": "medium",
    "high_best": "high",
    "recompose": "recompose",
    "recompose_bold": "bold",
}
LABEL_CN = {
    "low_best": "low · 只修瑕",
    "medium_best": "medium · 锁机位小优化",
    "high_best": "high · 跃升",
    "recompose": "recompose · 改机位",
    "recompose_bold": "大改 · 风格跳",
}
CASE_CN = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}
SIZE = {
    "9:16": "1024x1536",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
    "1:1": "1024x1024",
}
WORKERS = 5


def best_overlay(best_doc: dict, bot: dict) -> str:
    mode = bot.get("prompt_mode") or "none"
    if mode == "style_jump":
        by = (best_doc.get("by_scale") or {}).get("recompose_bold") or {}
        return str(by.get(bot.get("case_id") or "") or by.get("_default") or "")
    if mode != "best":
        return ""
    api = bot.get("api_scale") or "medium"
    by = (best_doc.get("by_scale") or {}).get(api) or {}
    return str(by.get(bot.get("case_id") or "") or by.get("_default") or "")


def compose_prompt(bot: dict, best_doc: dict) -> str:
    api = bot["api_scale"]
    mode = bot.get("prompt_mode") or "none"
    recompose_dir = bot.get("recompose_dir") or ""
    ar = bot.get("aspect_ratio") or ""
    base = " | ".join(
        x for x in (bot.get("gen_description"), bot.get("goal"), best_overlay(best_doc, bot)) if x
    )
    base = strip_affirmative_locks_from_prompt(base, scale=api)
    if mode == "style_jump":
        tail = "约束：仅保留主体剪影与画幅比；风格圣经按目标大跳；禁止混装旧机位与保色板套话"
        if ar:
            tail = f"约束：画幅 {ar}；仅保留主体剪影；风格圣经按目标大跳；禁止混装旧机位与保色板套话"
        composed = " | ".join(x for x in (base, tail) if x)
        composed = re.sub(r"(?:约束：)?保持原图画风笔触与色板；?", "", composed)
        composed = re.sub(r"保画风色板，按「[^」]*」重构机位\s*\|\s*", "", composed)
        composed = re.sub(r"\s*\|\s*\|\s*", " | ", composed).strip(" |")
        return composed[:3500]
    prof = get_converge_scale_profile(
        api,
        recompose_dir=recompose_dir,
        goal=bot.get("goal") or "",
        ref_image=bot.get("ref_image") or "",
        module=bot.get("module") or "",
    )
    return compose_style_first_prompt(base, prof)[:3500]


def select_bots() -> list[dict]:
    doc = json.loads((REPO / "bot_tasks_v8.json").read_text(encoding="utf-8"))
    bots = [b for b in doc["bots"] if b.get("display_scale") in WANT]
    order = {s: i for i, s in enumerate(WANT)}
    case_order = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
    bots.sort(key=lambda b: (case_order.index(b["slug"]), order[b["display_scale"]]))
    return bots


def _multipart(fields: dict[str, str], image_bytes: bytes, filename: str, mime: str) -> tuple[bytes, str]:
    boundary = "----rerun-" + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode()
        )
    body.extend(
        f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        f"Content-Type: {mime}\r\n\r\n".encode()
    )
    body.extend(image_bytes)
    body.extend(f"\r\n--{boundary}--\r\n".encode())
    return bytes(body), "multipart/form-data; boundary=" + boundary


def edit_once(src: Path, prompt: str, size: str, out: Path) -> None:
    mime = mimetypes.guess_type(src.name)[0] or "image/png"
    raw = src.read_bytes()
    fields = {
        "prompt": prompt,
        "model": MODEL,
        "n": "1",
        "quality": "high",
        "size": size,
        "response_format": "b64_json",
    }
    payload, ctype = _multipart(fields, raw, src.name, mime)
    bases = [CFG["base_url"], CFG.get("fallback_base_url")]
    last = "no response"
    for base in filter(None, bases):
        url = base.rstrip("/") + "/images/edits"
        req = urllib.request.Request(
            url,
            data=payload,
            method="POST",
            headers={"Authorization": "Bearer " + CFG["key"], "Content-Type": ctype},
        )
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code}: {e.read()[:240].decode('utf-8', 'ignore')}"
            if e.code in (429, 500, 502, 503, 504):
                time.sleep(4)
                continue
            raise RuntimeError(last) from e
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
            time.sleep(3)
            continue
        b64 = ((data.get("data") or [{}])[0]).get("b64_json")
        if not b64:
            raise RuntimeError("no b64_json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(b64))
        return
    raise RuntimeError(last)


def run_one(bot: dict, prompt: str) -> dict:
    slug = bot["slug"]
    scale = bot["display_scale"]
    short = LABEL[scale]
    out = OUT / "images" / f"{slug}_{short}.png"
    ref = REPO / bot["ref_image"]
    size = SIZE.get(bot.get("aspect_ratio") or "1:1", "1024x1024")
    print(f"GEN {bot['bot_id']} {slug} {short}", flush=True)
    err = ""
    ok = False
    for attempt in range(1, 4):
        try:
            edit_once(ref, prompt, size, out)
            ok = out.is_file() and out.stat().st_size > 1000
            if ok:
                break
            err = "empty file"
        except Exception as e:
            err = f"{type(e).__name__}: {e}"[:400]
            print(f"  retry {attempt} {slug} {short}: {err[:160]}", flush=True)
            time.sleep(3 * attempt)
    print(f"{'OK' if ok else 'FAIL'} {slug} {short} bytes={out.stat().st_size if out.is_file() else 0}", flush=True)
    return {
        "bot_id": bot["bot_id"],
        "slug": slug,
        "case": CASE_CN[slug],
        "display_scale": scale,
        "label": LABEL_CN[scale],
        "file": f"images/{out.name}" if ok else "",
        "ok": ok,
        "error": err,
        "prompt": prompt,
        "aspect_ratio": bot.get("aspect_ratio"),
        "ref": bot["ref_image"],
    }


def copy_refs(bots: list[dict]) -> dict[str, str]:
    seen: dict[str, str] = {}
    for b in bots:
        slug = b["slug"]
        if slug in seen:
            continue
        src = REPO / b["ref_image"]
        dst = OUT / "images" / f"{slug}_ref{src.suffix.lower()}"
        shutil.copy2(src, dst)
        seen[slug] = f"images/{dst.name}"
    return seen


def write_html(rows: list[dict], refs: dict[str, str]) -> Path:
    by_case: dict[str, list[dict]] = {}
    for row in rows:
        by_case.setdefault(row["slug"], []).append(row)
    sections = []
    for slug, items in by_case.items():
        items.sort(key=lambda r: WANT.index(r["display_scale"]))
        cards = [
            f"""<figure class="card ref">
  <figcaption>原图</figcaption>
  <img src="{refs[slug]}" alt="{CASE_CN[slug]} 原图">
</figure>"""
        ]
        for it in items:
            if it["ok"]:
                body = f'<img src="{it["file"]}" alt="{it["label"]}">'
            else:
                body = f'<p class="err">出图失败<br>{it["error"][:180]}</p>'
            cards.append(
                f"""<figure class="card">
  <figcaption>{it["label"]}</figcaption>
  {body}
  <details><summary>本档提示词</summary><p>{it["prompt"].replace("<", "&lt;")}</p></details>
</figure>"""
            )
        sections.append(
            f"""<section>
  <h2>{CASE_CN[slug]}</h2>
  <div class="row">{''.join(cards)}</div>
</section>"""
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
  p.note {{ color: #aaa; max-width: 920px; line-height: 1.5; }}
  section {{ padding: 8px 20px 28px; }}
  h2 {{ font-size: 16px; margin: 12px 8px; }}
  .row {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }}
  .card {{ margin: 0; background: #1e1e1e; border: 1px solid #333; padding: 8px; }}
  .card.ref {{ border-color: #6a5a3a; }}
  figcaption {{ font-size: 12px; margin-bottom: 6px; color: #ddd; }}
  img {{ width: 100%; height: auto; display: block; background: #0e0e0e; }}
  details {{ margin-top: 6px; font-size: 11px; color: #9a9a9a; }}
  details p {{ white-space: pre-wrap; }}
  .err {{ color: #f0a0a0; font-size: 12px; }}
</style>
</head>
<body>
<header>
  <h1>案例 01–04 原图 × 五档重出</h1>
  <p class="note">模型 gpt-image-2.5-sunburst，参考图走 edits。每格只出 1 轮，用来横看 low / medium / high / recompose / 大改的差别。主页上的旧分数来自最多 8 轮收敛，这一页没有沿用那些分。</p>
</header>
{''.join(sections)}
</body>
</html>
"""
    path = OUT / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> int:
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    bots = select_bots()
    jobs = [(b, compose_prompt(b, best)) for b in bots]
    refs = copy_refs(bots)
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_one, b, p) for b, p in jobs]
        for fut in as_completed(futs):
            rows.append(fut.result())
    rows.sort(key=lambda r: (r["slug"], WANT.index(r["display_scale"])))
    (OUT / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    page = write_html(rows, refs)
    ok = sum(1 for r in rows if r["ok"])
    print(f"DONE {ok}/{len(rows)} -> {page}")
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
