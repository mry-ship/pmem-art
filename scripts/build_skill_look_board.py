#!/usr/bin/env python3
"""Build HTML board from generated_v8_20_skill_look/look_state.json (Agent/VLM scores, real rounds)."""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_STATE = REPO / "generated_v8_20_skill_look" / "look_state.json"
DEFAULT_OUT = REPO / "docs" / "showcase" / "skill_look_20" / "index.html"
ASSETS = Path(r"C:\Users\ZhengLangPC\.cursor\projects\c-Users-ZhengLangPC-Desktop-Cursor-Pmem-Art\assets")


def _copy_into_board(src: Path, img_dir: Path, dest_name: str | None = None) -> str:
    """Copy a local image next to the HTML so file:// pages can see it."""
    if not src.is_file():
        return ""
    img_dir.mkdir(parents=True, exist_ok=True)
    name = dest_name or src.name
    dest = img_dir / name
    if not dest.exists() or dest.stat().st_mtime < src.stat().st_mtime or dest.stat().st_size != src.stat().st_size:
        shutil.copy2(src, dest)
    return f"images/{name}"


def rel_img(path: str, img_dir: Path) -> str:
    p = Path(path)
    if not p.is_file():
        cand = REPO / path
        if cand.is_file():
            p = cand
        elif ASSETS.joinpath(Path(path).name).is_file():
            p = ASSETS / Path(path).name
        else:
            return ""
    return _copy_into_board(p.resolve(), img_dir)

SLUG_TITLE = {
    "night_city": "案例 01 · 仙侠不夜城",
    "pastel_sketch": "案例 02 · 粉彩速写少女",
    "sunlit_portrait": "案例 03 · 窗边日光胸像",
    "ishtar_canyon": "案例 04 · 天井峡谷概念",
}
SCALE_LABEL = {
    "low_best": "low · 只修瑕",
    "medium_best": "medium · 锁机位",
    "high_best": "high · 跃升",
    "recompose": "recompose · 改机位",
    "recompose_bold": "大改 · 风格跳",
}


def score_class(t: float | None) -> str:
    if t is None:
        return ""
    if t >= 9.5:
        return "hit"
    if t >= 8.5:
        return "mid"
    return "low"


def build(state_path: Path, out_path: Path) -> None:
    state_path = state_path.resolve()
    out_path = out_path.resolve()
    img_dir = out_path.parent / "images"
    repo = REPO.resolve()
    state = json.loads(state_path.read_text(encoding="utf-8"))
    try:
        state_rel = state_path.relative_to(repo).as_posix()
    except ValueError:
        state_rel = state_path.as_posix()
    rows_by_slug: dict[str, list] = {}
    for bid, st in state.get("bots", {}).items():
        bot = st.get("bot") or {}
        slug = bot.get("slug") or "other"
        best = st.get("best_round") or {}
        n = len(st.get("rounds") or [])
        img = best.get("image") or ""
        rows_by_slug.setdefault(slug, []).append(
            {
                "id": bid,
                "scale": bot.get("display_scale") or "",
                "status": st.get("status"),
                "rounds": n,
                "next": st.get("next_round"),
                "stop": st.get("stop_reason") or "",
                "best_total": best.get("total"),
                "best_r": best.get("round"),
                "img": rel_img(img, img_dir) if img else "",
                "ref": rel_img(str((REPO / bot.get("ref_image", "")).resolve()), img_dir),
            }
        )

    sections = []
    for slug in ("night_city", "pastel_sketch", "sunlit_portrait", "ishtar_canyon"):
        cards = rows_by_slug.get(slug, [])
        cards.sort(key=lambda c: c["id"])
        figs = []
        ref = cards[0]["ref"] if cards else ""
        if ref:
            figs.append(
                f'<figure class="card ref"><figcaption>原图</figcaption>'
                f'<img src="{html.escape(ref, quote=True)}" alt="ref"></figure>'
            )
        for c in cards:
            lab = SCALE_LABEL.get(c["scale"], c["scale"])
            t = c["best_total"]
            cls = score_class(t if t is not None else None)
            meta = f'{c["rounds"]} 轮 · next R{c["next"]} · best R{c["best_r"] or "-"}'
            if c["stop"]:
                meta += f' · {html.escape(c["stop"])}'
            src = html.escape(c["img"], quote=True) if c["img"] else ""
            img_tag = f'<img src="{src}" alt="">' if src else '<p class="err">无终稿图</p>'
            figs.append(
                f'<figure class="card"><figcaption>{html.escape(lab)} · {html.escape(c["id"])}</figcaption>'
                f'<div class="shot"><span class="total {cls}">{t if t is not None else "—"}</span>'
                f"{img_tag}"
                f"</div><p class='extra'>{meta} · judge: {html.escape(state.get('judge') or '')}</p></figure>"
            )
        sections.append(
            f"<section><h2>{html.escape(SLUG_TITLE.get(slug, slug))}</h2>"
            f'<div class="row">{"".join(figs)}</div></section>'
        )

    doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>Skill Look · 20 路真实轮次</title>
<style>
body{{margin:0;background:#141414;color:#eee;font-family:"Segoe UI","PingFang SC",sans-serif}}
header{{padding:24px 28px 8px}} h1{{font-size:22px;margin:0 0 8px}}
p.note{{color:#aaa;max-width:1100px;line-height:1.55;font-size:13px}}
section{{padding:8px 20px 28px}} h2{{font-size:16px;margin:12px 8px}}
.row{{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px}}
.card{{margin:0;background:#1e1e1e;border:1px solid #333;padding:8px}}
.card.ref{{border-color:#6a5a3a}} figcaption{{font-size:11px;margin-bottom:6px;color:#ddd}}
.shot{{position:relative}} .total{{position:absolute;top:8px;left:8px;z-index:1;font-weight:650;background:rgba(0,0,0,.65);padding:2px 7px;border-radius:4px;font-size:13px}}
.total.hit{{color:#8fd18f}} .total.mid{{color:#e6c36a}} .total.low{{color:#e0a0a0}}
img{{width:100%;height:auto;display:block;background:#0e0e0e}}
.extra{{margin:6px 0 0;font-size:10px;color:#aaa;line-height:1.35}}
.err{{color:#f0a0a0;font-size:11px}}
</style></head><body>
<header>
<h1>Skill Look · 20 张五档（Agent/VLM 主评 · 真实轮次）</h1>
<p class="note">数据源：<code>{html.escape(state_rel)}</code>。
主分来自闭环 record（VLM 优先 → 无则 Agent 看图）；离线 Absolute-5D 仅旁证，不参与 STOP。
生图：apikey.fan 优先，余额不足时走 Cursor 默认 GenerateImage 任务。
阈值 ≥{state.get('threshold', 9.5)} · anatomy ≥{state.get('anat_gate', 7.5)} · max {state.get('max_rounds', 8)} 轮。</p>
</header>
{"".join(sections)}
</body></html>"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    print(out_path.resolve())


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--state", type=Path, default=DEFAULT_STATE)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    build(args.state, args.out)
