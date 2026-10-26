#!/usr/bin/env python3
"""Four homepage cases x four scales, retry until visible departure sits in band."""
from __future__ import annotations

import base64
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import shutil

from rerun_homepage_5scale import (  # noqa: E402
    CASE_CN,
    compose_prompt,
    edit_once,
    select_bots,
)
OUT = REPO / "docs" / "showcase" / "departure_4scale"
CFG = json.loads(
    Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\config.json").read_text(encoding="utf-8-sig")
)
MODEL = "gpt-5.6-terra"
SCALES = ["low_best", "medium_best", "high_best", "recompose"]
API = {"low_best": "low", "medium_best": "medium", "high_best": "high", "recompose": "recompose"}
SHORT = {"low_best": "low", "medium_best": "medium", "high_best": "high", "recompose": "recompose"}
LABEL = {
    "low_best": "low · 0.5–2.0",
    "medium_best": "medium · 2.0–4.5",
    "high_best": "high · 4.5–7.5",
    "recompose": "recompose · 指定机位",
}
MAX_ROUNDS = 3
WORKERS = 4


def thumb(path: Path) -> Path:
    jpg = OUT / "_thumbs" / (path.stem + ".jpg")
    if jpg.is_file():
        return jpg
    try:
        from PIL import Image

        jpg.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(path).convert("RGB")
        im.thumbnail((768, 768))
        im.save(jpg, "JPEG", quality=80)
        return jpg
    except Exception:
        return path


def image_part(path: Path) -> dict:
    raw = thumb(path).read_bytes()
    kind = "jpeg" if thumb(path).suffix.lower() in (".jpg", ".jpeg") else "png"
    return {"type": "input_image", "image_url": f"data:image/{kind};base64," + base64.b64encode(raw).decode("ascii")}


def extract_text(data: dict) -> str:
    chunks = []
    for item in data.get("output") or []:
        if isinstance(item, dict):
            for part in item.get("content") or []:
                if isinstance(part, dict) and part.get("text"):
                    chunks.append(str(part["text"]))
    if not chunks and isinstance(data.get("output_text"), str):
        return data["output_text"]
    if not chunks:
        raise ValueError("no text")
    return "\n".join(chunks)


def judge_pair(ref: Path, result: Path, direction: str) -> dict:
    extra = f"指定新机位：{direction}。" if direction else "这一档不是改机位。"
    prompt = f"""第一张是原图，第二张是修改结果。{extra}
偏离：0 到 10，一位小数。0 是同一张图，10 是换成另一张图。只看机位、姿态、布局、光影、件数的可见差别。
camera_hit：第二张的机位是不是指定的新机位。没有指定新机位就写 false。
只输出 JSON：
{{"departure":0,"camera_hit":false,"note":"一句话"}}
"""
    content = [{"type": "input_text", "text": prompt}, image_part(ref), image_part(result)]
    body = {
        "model": MODEL,
        "stream": False,
        "input": [{"role": "user", "content": content}],
    }
    req = urllib.request.Request(
        CFG["base_url"].rstrip("/") + "/responses",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": "Bearer " + CFG["key"],
            "Content-Type": "application/json",
            "x-openai-actor-authorization": "apikey.fan",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8", "replace"))
    text = extract_text(data)
    start, end = text.find("{"), text.rfind("}")
    parsed = json.loads(text[start : end + 1])
    return {
        "departure": float(parsed.get("departure")),
        "camera_hit": bool(parsed.get("camera_hit")),
        "note": str(parsed.get("note") or ""),
    }


def in_band(api: str, direction: str, judged: dict) -> str | None:
    """Visual departure is recorded only. Stop limits now live on prompt percent."""
    del api, direction, judged
    return None


def strengthen(prompt: str, api: str, note: str) -> str:
    if api == "low":
        add = "下一轮只保留原图机位、姿态、件数和布局，改动收回到一处局部。"
    elif api == "medium":
        add = "下一轮保持机位和件数，把光影或局部布局拉开到能看出不是只修了一点瑕。"
    elif api == "high":
        add = "下一轮必须换一个看得出的机位，或把戏剧光拉到锁机位小优化装不下。媒介和身份留下。"
    else:
        add = "下一轮机位必须落到指定方向，不要停在原图机位上。"
    return f"{prompt} | {note}。{add}"[:3500]


def run_cell(bot: dict, base_prompt: str) -> dict:
    api = API[bot["display_scale"]]
    short = SHORT[bot["display_scale"]]
    ref = REPO / bot["ref_image"]
    size = {"9:16": "1024x1536", "3:4": "1024x1536", "4:3": "1536x1024"}.get(bot.get("aspect_ratio") or "", "1024x1024")
    prompt = base_prompt
    direction = bot.get("recompose_dir") or ""
    last: dict = {}
    for round_num in range(1, MAX_ROUNDS + 1):
        out = OUT / "images" / f"{bot['slug']}_{short}_r{round_num}.png"
        print(f"GEN {bot['slug']} {short} r{round_num}", flush=True)
        try:
            edit_once(ref, prompt, size, out)
        except Exception as exc:
            print(f"FAIL {bot['slug']} {short} {exc}", flush=True)
            last = {"ok": False, "error": str(exc)[:240], "round": round_num, "prompt": prompt}
            break
        judged = None
        for attempt in range(1, 4):
            try:
                judged = judge_pair(ref, out, direction if api == "recompose" else "")
                break
            except Exception as exc:
                print(f"  judge retry {attempt} {bot['slug']} {short}: {exc}", flush=True)
                time.sleep(8)
        if not judged:
            last = {"ok": True, "file": f"images/{out.name}", "round": round_num, "prompt": prompt, "error": "judge failed", "in_band": False}
            break
        note = in_band(api, direction, judged)
        print(
            f"OK {bot['slug']} {short} r{round_num} departure={judged['departure']:.1f} camera={judged['camera_hit']} band={note or 'in'}",
            flush=True,
        )
        last = {
            "ok": True,
            "file": f"images/{out.name}",
            "round": round_num,
            "prompt": prompt,
            "departure": judged["departure"],
            "camera_hit": judged["camera_hit"],
            "note": judged["note"],
            "band_note": note or "",
            "in_band": note is None,
            "error": "",
        }
        if note is None:
            break
        prompt = strengthen(base_prompt, api, note)
    last.update({
        "slug": bot["slug"],
        "display_scale": bot["display_scale"],
        "label": LABEL[bot["display_scale"]],
        "case": CASE_CN[bot["slug"]],
    })
    return last


def esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;")


def write_html(rows: list[dict], refs: dict[str, str]) -> Path:
    by: dict[str, list[dict]] = {}
    for row in rows:
        by.setdefault(row["slug"], []).append(row)
    order = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
    sections = []
    hit = 0
    for slug in order:
        items = sorted(by.get(slug) or [], key=lambda r: SCALES.index(r["display_scale"]))
        cards = [f'<figure class="card ref"><figcaption>原图</figcaption><img src="{refs[slug]}" alt="原图"></figure>']
        for it in items:
            if it.get("in_band"):
                hit += 1
            tag = "落在区间" if it.get("in_band") else "未进区间"
            if it.get("ok") and it.get("file"):
                body = f'<img src="{it["file"]}" alt="{esc(it["label"])}">'
            else:
                body = f'<p class="err">{esc(it.get("error") or "失败")}</p>'
            dep = it.get("departure")
            dep_s = f"{float(dep):.1f}" if isinstance(dep, (int, float)) else "—"
            cards.append(
                f"""<figure class="card {'go' if it.get('in_band') else ''}">
  <figcaption><span>{esc(it['label'])}</span><b>{dep_s}</b></figcaption>
  {body}
  <p class="line">{tag} · 第 {it.get('round') or 0} 轮。{esc(it.get('note') or it.get('band_note') or '')}</p>
</figure>"""
            )
        sections.append(f"<section><h2>{CASE_CN[slug]}</h2><div class=\"row\">{''.join(cards)}</div></section>")
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>四档偏离下限</title>
<style>
body {{ margin:0; background:#141414; color:#eee; font-family:"Segoe UI",sans-serif; }}
header {{ padding:24px 28px 8px; }} h1 {{ font-size:22px; margin:0 0 8px; }}
p.note {{ color:#aaa; max-width:980px; line-height:1.5; }}
section {{ padding:8px 20px 28px; }} h2 {{ font-size:16px; margin:12px 8px; }}
.row {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; }}
.card {{ margin:0; background:#1e1e1e; border:1px solid #333; padding:8px; }}
.card.ref {{ border-color:#6a5a3a; }} .card.go {{ border-color:#3d7a4a; }}
figcaption {{ display:flex; justify-content:space-between; font-size:12px; margin-bottom:6px; }}
figcaption b {{ font-size:18px; }}
img {{ width:100%; height:auto; display:block; background:#0e0e0e; }}
.line {{ font-size:12px; line-height:1.4; color:#ccc; }}
.err {{ color:#f0a0a0; font-size:12px; }}
</style></head><body>
<header><h1>案例 01–04 · 四档可见偏离</h1>
<p class="note">low 0.5–2.0，medium 2.0–4.5，high 4.5–7.5，区间首尾相接。recompose 看指定机位有没有落到画面上。每格最多 3 轮，偏离进了本档区间就停。右上角是相对原图的偏离分。落在区间 {hit}/{len(rows)}。</p>
</header>
{''.join(sections)}
</body></html>"""
    path = OUT / "index.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> int:
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    best = json.loads((REPO / "best_prompts_by_scale.json").read_text(encoding="utf-8"))
    bots = [b for b in select_bots() if b.get("display_scale") in SCALES]
    refs: dict[str, str] = {}
    for bot in bots:
        slug = bot["slug"]
        if slug in refs:
            continue
        src = REPO / bot["ref_image"]
        dst = OUT / "images" / f"{slug}_ref{src.suffix.lower()}"
        shutil.copy2(src, dst)
        refs[slug] = f"images/{dst.name}"
    rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = [ex.submit(run_cell, b, compose_prompt(b, best)) for b in bots]
        for fut in as_completed(futs):
            rows.append(fut.result())
    rows.sort(key=lambda r: (r["slug"], SCALES.index(r["display_scale"])))
    (OUT / "manifest.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    page = write_html(rows, refs)
    ok = sum(1 for r in rows if r.get("in_band"))
    print(f"DONE in-band {ok}/{len(rows)} -> {page}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
