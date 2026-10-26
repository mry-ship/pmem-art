#!/usr/bin/env python3
"""Three-part gate for the homepage rerun board.

Fidelity is image-only. Task fit and pairwise preference see the original
and the scale contract. No 0-10 beauty score.
"""
from __future__ import annotations

import base64
import json
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BOARD = REPO / "docs" / "showcase" / "rerun_5scale"
CFG = json.loads(Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-openai\config.json").read_text(encoding="utf-8-sig"))
THUMBS = BOARD / "_thumbs"
WORKERS = 1
CASE_ORDER = ["night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"]
SCALE_ORDER = ["low_best", "medium_best", "high_best", "recompose", "recompose_bold"]
CASE_CN = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}
TASK = {
    "low_best": "只修局部瑕疵。机位、姿态、主体数量和布局必须保持。",
    "medium_best": "机位保持。允许小幅姿态、局部布局和光影调整。",
    "high_best": "可以换机位和戏剧光影，媒介与主体身份必须还在。",
    "recompose": "必须改成指定的新机位，画风和身份仍要在。",
    "recompose_bold": "风格必须明显跳开，只保留主体剪影，不要守着原图色板。",
}

FIDELITY_PROMPT = """只看这一张图。打一个保真分，0 到 10，保留一位小数。
这个分只看硬伤和完成度，不要因为好看、风格或氛围加分。
硬伤：多出来的手或肢体、明显接错的关节、透视互相打架、主体残缺到认不出。有硬伤时分数不超过 4。
未完成：结构线还露着、手脚或建筑只铺了调子没交实、大面积空白或草稿线。故意的素描笔触如果形体已经交实，不算未完成。未完成时分数不超过 6。
没有硬伤也没有未完成，分数从 7 起。10 是形体、透视和完成度都站得住。
只输出 JSON：
{"score":7.0,"hard_fail":false,"unfinished":false,"note":"指出具体问题，没有就写已交实"}
"""


def task_prompt(scale: str, direction: str) -> str:
    rule = TASK[scale]
    extra = f"指定新机位：{direction}。" if scale == "recompose" and direction else ""
    return f"""第一张是原图，第二张是修改结果。这一档只要求：{rule}{extra}
打两个分，都是 0 到 10，保留一位小数。不要打好看总分。
task_score：第二张把这一档做到了多少。10 是完全按这一档，0 是完全没按。
pair_score：按这一档交稿，第二张相对第一张有多合适。5 是一样。高于 5 改图更合适，低于 5 原图更合适。
task_met：task_score 达到 7 才是 true。
prefer：pair_score 高于 5 写 result，低于 5 写 ref，等于 5 写 tie。
只输出 JSON：
{{"task_score":0,"pair_score":5,"task_met":false,"prefer":"ref","why":"一句话"}}
"""


def thumb(path: Path) -> Path:
    jpg = THUMBS / (path.stem + ".jpg")
    return jpg if jpg.is_file() else path


def num(value) -> float | None:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if score != score:
        return None
    return round(max(0.0, min(10.0, score)), 1)


def fmt(score) -> str:
    return "—" if score is None else f"{float(score):.1f}"


def parse_obj(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no json")
    return json.loads(text[start : end + 1])


def image_part(path: Path) -> dict:
    raw = thumb(path).read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"}


def extract_text(data: dict) -> str:
    chunks = []
    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue
        for part in item.get("content") or []:
            if isinstance(part, dict) and part.get("text"):
                chunks.append(str(part["text"]))
    if not chunks and isinstance(data.get("output_text"), str):
        chunks.append(data["output_text"])
    if not chunks:
        raise ValueError("no text")
    return "\n".join(chunks)


def call_gpt(images: list[Path], prompt: str) -> tuple[dict, str]:
    # astra / sol currently drop the connection at 60s. terra answers vision calls.
    model = "gpt-5.6-terra"
    content = [{"type": "input_text", "text": prompt}]
    content.extend(image_part(p) for p in images)
    body = {
        "model": model,
        "stream": False,
        "input": [{"role": "user", "content": content}],
    }
    last = ""
    for attempt in range(1, 4):
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
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8", "replace"))
            if data.get("status") == "failed" or data.get("error"):
                raise RuntimeError(json.dumps(data.get("error") or data.get("status"), ensure_ascii=False)[:180])
            return parse_obj(extract_text(data)), str(data.get("model") or model)
        except Exception as exc:
            msg = exc.read().decode("utf-8", "replace")[:160] if isinstance(exc, urllib.error.HTTPError) else str(exc)
            last = f"{type(exc).__name__}: {msg}"[:180]
            print(f"  retry {attempt} {model}: {last[:110]}", flush=True)
            time.sleep(8)
    raise RuntimeError(last or "score failed")


def fidelity_of(path: Path) -> dict:
    print(f"FIDELITY {path.name}", flush=True)
    try:
        data, model = call_gpt([path], FIDELITY_PROMPT)
        score = num(data.get("score"))
        if score is None:
            raise ValueError("no score")
        hard = bool(data.get("hard_fail"))
        unfinished = bool(data.get("unfinished"))
        if hard:
            state = "硬伤"
        elif unfinished:
            state = "未完成"
        else:
            state = "通过"
        print(f"OK {path.name} {state} {score:.1f}", flush=True)
        return {"ok": True, "score": score, "state": state, "hard_fail": hard, "unfinished": unfinished,
                "note": str(data.get("note") or ""), "model": model}
    except Exception as exc:
        print(f"FAIL {path.name} {exc}", flush=True)
        return {"ok": False, "error": str(exc)[:240], "state": "失败", "note": ""}


def compare_of(ref: Path, result: Path, scale: str, direction: str) -> dict:
    print(f"COMPARE {result.name}", flush=True)
    try:
        data, model = call_gpt([ref, result], task_prompt(scale, direction))
        task_score = num(data.get("task_score"))
        pair_score = num(data.get("pair_score"))
        if task_score is None or pair_score is None:
            raise ValueError("no score")
        if pair_score > 5:
            prefer = "result"
        elif pair_score < 5:
            prefer = "ref"
        else:
            prefer = "tie"
        task_met = task_score >= 7
        print(f"OK {result.name} task={task_score:.1f} pair={pair_score:.1f}", flush=True)
        return {"ok": True, "task_score": task_score, "pair_score": pair_score,
                "task_met": task_met, "prefer": prefer,
                "why": str(data.get("why") or ""), "model": model}
    except Exception as exc:
        print(f"FAIL {result.name} {exc}", flush=True)
        return {"ok": False, "error": str(exc)[:240], "task_met": False, "prefer": "tie", "why": ""}


def directions() -> dict[str, str]:
    bots = json.loads((REPO / "bot_tasks_v8.json").read_text(encoding="utf-8"))["bots"]
    return {b["bot_id"]: b.get("recompose_dir") or "" for b in bots}


def ref_path(slug: str) -> Path:
    return next((BOARD / "images").glob(slug + "_ref.*"))


def deliverable(fid: dict, comp: dict | None) -> bool:
    if not fid.get("ok") or fid.get("state") != "通过":
        return False
    if comp is None:
        return False
    return bool(comp.get("ok") and comp.get("task_met") and comp.get("prefer") == "result")


def esc(text: str) -> str:
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render(rows: list[dict], fidelity: dict, compare: dict) -> None:
    by_case: dict[str, list[dict]] = {}
    for row in rows:
        by_case.setdefault(row["slug"], []).append(row)
    sections = []
    n_ok = 0
    n_gen = 0
    for slug in CASE_ORDER:
        items = sorted(by_case.get(slug) or [], key=lambda r: SCALE_ORDER.index(r["display_scale"]))
        ref_name = ref_path(slug).name
        cards = [card(slug, "原图", ref_name, fidelity.get(ref_name) or {}, None, "")]
        for it in items:
            name = Path(it["file"]).name
            n_gen += 1
            comp = compare.get(name) or {}
            if deliverable(fidelity.get(name) or {}, comp):
                n_ok += 1
            cards.append(card(slug, it["label"], name, fidelity.get(name) or {}, comp, it.get("prompt") or ""))
        sections.append(f"<section><h2>{CASE_CN[slug]}</h2><div class=\"row\">{''.join(cards)}</div></section>")
    note = (
        "三项分开打分，都是 0 到 10。保真只看单张的硬伤和完成度，好看不加分。"
        "任务分是这一档做到多少。并排分以 5 为和原图一样，高于 5 改图更适合这一档。"
        f"三项都过线的修改图 {n_ok}/{n_gen}。模型 gpt-5.6-terra。"
    )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>案例 01–04 · 三关打分</title>
<style>
  body {{ margin: 0; background: #141414; color: #eee; font-family: "Segoe UI", sans-serif; }}
  header {{ padding: 24px 28px 8px; }}
  h1 {{ font-size: 22px; margin: 0 0 8px; }}
  p.note {{ color: #aaa; max-width: 980px; line-height: 1.5; }}
  section {{ padding: 8px 20px 28px; }}
  h2 {{ font-size: 16px; margin: 12px 8px; }}
  .row {{ display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; }}
  .card {{ margin: 0; background: #1e1e1e; border: 1px solid #333; padding: 8px; }}
  .card.ref {{ border-color: #6a5a3a; }}
  .card.go {{ border-color: #3d7a4a; }}
  figcaption {{ font-size: 12px; margin-bottom: 6px; display: flex; justify-content: space-between; gap: 6px; }}
  .tag {{ font-weight: 650; }}
  .go-tag {{ color: #8fd18f; }}
  .stop-tag {{ color: #e0a0a0; }}
  .scores {{ display: flex; gap: 10px; margin-top: 8px; }}
  .scores div {{ min-width: 42px; }}
  .scores b {{ display: block; font-size: 18px; line-height: 1.1; }}
  .scores span {{ font-size: 11px; color: #9a9a9a; }}
  img {{ width: 100%; height: auto; display: block; background: #0e0e0e; }}
  .line {{ margin-top: 6px; font-size: 12px; line-height: 1.4; }}
  .muted {{ color: #9a9a9a; }}
  details {{ margin-top: 6px; font-size: 11px; color: #9a9a9a; }}
  details p {{ white-space: pre-wrap; }}
</style>
</head>
<body>
<header>
  <h1>案例 01–04 · 保真 / 任务 / 并排</h1>
  <p class="note">{esc(note)}</p>
</header>
{''.join(sections)}
</body>
</html>
"""
    (BOARD / "index.html").write_text(html, encoding="utf-8")


def score_row(fid: dict, comp: dict | None) -> str:
    cells = [f"<div><b>{fmt(fid.get('score'))}</b><span>保真</span></div>"]
    if comp is not None:
        cells.append(f"<div><b>{fmt(comp.get('task_score'))}</b><span>任务</span></div>")
        cells.append(f"<div><b>{fmt(comp.get('pair_score'))}</b><span>并排</span></div>")
    return f"<div class=\"scores\">{''.join(cells)}</div>"


def card(slug: str, label: str, filename: str, fid: dict, comp: dict | None, prompt: str) -> str:
    ref_cls = " ref" if comp is None else ""
    ok = deliverable(fid, comp) if comp is not None else False
    if comp is None:
        tag = fid.get("state") or "失败"
        tag_cls = "go-tag" if fid.get("state") == "通过" else "stop-tag"
    else:
        tag = "三项过线" if ok else "未过线"
        tag_cls = "go-tag" if ok else "stop-tag"
        ref_cls = " go" if ok else ""
    lines = [f"<div class=\"line\">保真{esc(fid.get('state') or '失败')}。{esc(fid.get('note') or fid.get('error') or '')}</div>"]
    if comp is not None:
        lines.append(f"<div class=\"line muted\">{esc(comp.get('why') or comp.get('error') or '')}</div>")
    extra = f"<details><summary>本档提示词</summary><p>{esc(prompt)}</p></details>" if prompt else ""
    return f"""<figure class="card{ref_cls}">
  <figcaption><span>{esc(label)}</span><span class="tag {tag_cls}">{tag}</span></figcaption>
  <img src="images/{esc(filename)}" alt="{esc(CASE_CN.get(slug, slug) + ' ' + label)}">
  {score_row(fid, comp)}
  {''.join(lines)}
  {extra}
</figure>"""


def main() -> int:
    rows = json.loads((BOARD / "manifest.json").read_text(encoding="utf-8"))
    dirs = directions()
    fid_path = BOARD / "gate_fidelity.json"
    cmp_path = BOARD / "gate_compare.json"
    fidelity = json.loads(fid_path.read_text(encoding="utf-8")) if fid_path.is_file() else {}
    compare = json.loads(cmp_path.read_text(encoding="utf-8")) if cmp_path.is_file() else {}

    images = [ref_path(slug) for slug in CASE_ORDER]
    for row in rows:
        if row.get("ok") and row.get("file"):
            images.append(BOARD / row["file"])
    pending_f = [p for p in images if "score" not in (fidelity.get(p.name) or {})]
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {ex.submit(fidelity_of, p): p for p in pending_f}
        for fut in as_completed(futs):
            p = futs[fut]
            fidelity[p.name] = fut.result()
            fid_path.write_text(json.dumps(fidelity, ensure_ascii=False, indent=2), encoding="utf-8")

    pending_c = []
    for row in rows:
        if not row.get("ok"):
            continue
        name = Path(row["file"]).name
        if "task_score" in (compare.get(name) or {}):
            continue
        pending_c.append(row)
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futs = {
            ex.submit(compare_of, ref_path(row["slug"]), BOARD / row["file"], row["display_scale"], dirs.get(row["bot_id"], "")): row
            for row in pending_c
        }
        for fut in as_completed(futs):
            row = futs[fut]
            compare[Path(row["file"]).name] = fut.result()
            cmp_path.write_text(json.dumps(compare, ensure_ascii=False, indent=2), encoding="utf-8")

    render(rows, fidelity, compare)
    fid_ok = sum(1 for p in images if "score" in (fidelity.get(p.name) or {}))
    cmp_ok = sum(1 for row in rows if "task_score" in (compare.get(Path(row["file"]).name) or {}))
    print(f"DONE fidelity {fid_ok}/{len(images)} compare {cmp_ok}/{len(rows)} -> {BOARD / 'index.html'}")
    return 0 if fid_ok == len(images) and cmp_ok == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
