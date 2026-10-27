"""Clickable process board written at converge finish.

One HTML page: reference read, every discussion draft, every generated round
with scores, then a short conclusion. Clicking a picture opens it.
"""
from __future__ import annotations

import html
import shutil
from pathlib import Path
from typing import Any


def _esc(text: Any) -> str:
    return html.escape(str(text or ""), quote=True)


def _score(row: dict[str, Any]) -> float | None:
    try:
        val = row.get("score")
        return float(val) if val is not None else None
    except (TypeError, ValueError):
        return None


def _score_class(score: float | None) -> str:
    if score is None:
        return "mid"
    if score >= 9.6:
        return "hit"
    if score >= 8.5:
        return "mid"
    return "low"


def _find_image(root: Path, raw: str) -> Path | None:
    if not raw:
        return None
    cand = Path(raw)
    if not cand.is_absolute():
        cand = root / raw
    return cand if cand.is_file() else None


def _copy_image(src: Path, dest_dir: Path, stem: str) -> str:
    dest_dir.mkdir(parents=True, exist_ok=True)
    name = f"{stem}{src.suffix.lower() or '.png'}"
    dest = dest_dir / name
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)
    return name


def write_process_board(root: Path, sess: dict[str, Any], *, winner: dict[str, Any] | None = None) -> Path:
    """Write `.memory-art/converge/boards/<session>/index.html` and return that path."""
    root = Path(root)
    session_id = str(sess.get("session_id") or "session")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in session_id) or "session"
    board_dir = root / ".memory-art" / "converge" / "boards" / safe
    img_dir = board_dir / "images"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)

    win_round = int((winner or sess.get("winner") or {}).get("round") or 0)
    rounds = list(sess.get("rounds") or [])
    discussions = list(sess.get("discussions") or [])
    ref_name = ""
    ref_path = _find_image(root, str(sess.get("ref_image") or ""))
    if ref_path:
        ref_name = _copy_image(ref_path, img_dir, "ref")

    cards: list[str] = []
    for row in rounds:
        n = int(row.get("round") or 0)
        src = _find_image(root, str(row.get("image") or ""))
        shot = ""
        if src:
            name = _copy_image(src, img_dir, f"r{n}")
            shot = (
                f'<button type="button" class="shot" data-full="images/{_esc(name)}">'
                f'<img src="images/{_esc(name)}" alt="第 {n} 轮"></button>'
            )
        else:
            shot = '<p class="missing">这一轮没有找到图片文件</p>'
        sc = _score(row)
        sc_txt = "待审" if sc is None else f"{sc:.2f}"
        prev = next((r for r in rounds if int(r.get("round") or 0) == n - 1), None)
        bullets = []
        if prev and prev.get("next_fix"):
            bullets.append(f"这一轮要改：{prev.get('next_fix')}")
        if row.get("strengths"):
            bullets.append(f"亮点：{row.get('strengths')}")
        if row.get("defects"):
            bullets.append(f"不足：{row.get('defects')}")
        if row.get("next_fix"):
            bullets.append(f"下轮：{row.get('next_fix')}")
        lis = "".join(f"<li>{_esc(b)}</li>" for b in bullets) or "<li>这一轮没有写下评语</li>"
        win = " win" if n == win_round else ""
        cards.append(
            f'<figure class="card{win}">'
            f'<figcaption><b class="{_score_class(sc)}">第 {n} 轮 · {sc_txt}</b>'
            f'<span class="dims">{_esc(row.get("dims") or "未记五维")}</span></figcaption>'
            f'{shot}<ul>{lis}</ul></figure>'
        )

    talk_cards: list[str] = []
    for note in discussions:
        n = int(note.get("round") or 0)
        bits = []
        if note.get("strengths"):
            bits.append(f"说通了：{note.get('strengths')}")
        if note.get("defects"):
            bits.append(f"没过：{note.get('defects')}")
        if note.get("next_fix"):
            bits.append(f"下一稿：{note.get('next_fix')}")
        lis = "".join(f"<li>{_esc(b)}</li>" for b in bits)
        body = _esc(note.get("prompt") or note.get("text") or "")
        talk_cards.append(
            f'<article class="card talk"><h3>论述第 {n} 稿</h3>'
            f'<pre>{body}</pre><ul>{lis}</ul></article>'
        )

    sc_win = _score(winner or {}) if winner else None
    try:
        line = float(sess.get("accept_threshold") or sess.get("threshold") or 9.6)
    except (TypeError, ValueError):
        line = 9.6
    if winner:
        mark = "到线。" if sc_win is not None and sc_win >= line else f"未到 {line:.2f}。"
        total = "" if sc_win is None else f"{sc_win:.2f}"
        end = (
            f"胜出第 {int(winner.get('round') or 0)} 轮，总分 {total}。{mark}"
            f"{_esc(winner.get('defects') or '这一轮没有留下不足。')}"
        )
    else:
        end = "还没有胜出轮。"
    goal = _esc(sess.get("goal") or session_id)
    ref_block = ""
    if ref_name or sess.get("ref_analysis"):
        img = (
            f'<button type="button" class="shot" data-full="images/{_esc(ref_name)}">'
            f'<img src="images/{_esc(ref_name)}" alt="参考图"></button>'
            if ref_name else ""
        )
        ref_block = (
            f'<section><h2>参考图分析</h2><div class="row">'
            f'<figure class="card ref">{img}<p>{_esc(sess.get("ref_analysis") or "没有写下分析。")}</p>'
            f'</figure></div></section>'
        )
    talk_block = ""
    if talk_cards:
        talk_block = f'<section><h2>论述过程</h2><div class="row">{"".join(talk_cards)}</div></section>'
    rounds_block = (
        f'<section><h2>出图过程</h2><div class="row">{"".join(cards) or "<p>还没有出图轮。</p>"}</div></section>'
    )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>过程板 · {_esc(session_id)}</title>
<style>
body{{margin:0;background:#1b2430;color:#e8eef6;font-family:"Segoe UI","PingFang SC",sans-serif}}
header,section{{padding:18px 22px}} h1{{font-size:22px;margin:0 0 8px}} h2{{font-size:16px;margin:0 0 12px}}
.note{{color:#a9b6c6;font-size:13px;line-height:1.5;max-width:980px}}
.row{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:12px}}
.card{{margin:0;background:#243140;border:1px solid #334155;border-radius:8px;padding:10px}}
.card.win{{border:2px solid #e85d4c}} .card.ref{{border-color:#8a7344}}
figcaption b,.card h3{{display:block;font-size:14px;margin-bottom:4px}}
b.hit{{color:#8fd18f}} b.mid{{color:#e6c36a}} b.low{{color:#e0a0a0}}
.dims{{display:block;color:#c5d0dc;font-size:12px;line-height:1.4}}
.shot{{display:block;width:100%;padding:0;border:0;background:transparent;cursor:pointer}}
img{{width:100%;height:auto;display:block;background:#121820;border-radius:4px}}
ul{{margin:8px 0 0;padding-left:16px;font-size:12px;line-height:1.45;color:#d5deea}}
pre{{white-space:pre-wrap;font-size:12px;line-height:1.45;color:#d5deea;margin:0}}
.summary{{background:#243140;border-radius:8px;padding:12px 14px;line-height:1.5}}
.lightbox{{display:none;position:fixed;inset:0;background:rgba(0,0,0,.82);align-items:center;justify-content:center;z-index:5}}
.lightbox.open{{display:flex}} .lightbox img{{max-width:92vw;max-height:90vh;width:auto}}
</style></head><body>
<header>
<h1>{goal}</h1>
<p class="note">点图片看大图。红框是胜出轮。论述稿和出图轮都留在这一页。</p>
</header>
{ref_block}
{talk_block}
{rounds_block}
<section><h2>总结</h2><p class="summary">{end}</p></section>
<div class="lightbox" id="lightbox"><img alt=""></div>
<script>
const lb = document.getElementById("lightbox");
const big = lb.querySelector("img");
document.querySelectorAll(".shot").forEach(btn => btn.addEventListener("click", () => {{
  big.src = btn.dataset.full;
  lb.classList.add("open");
}}));
big.addEventListener("click", e => e.stopPropagation());
lb.addEventListener("click", () => lb.classList.remove("open"));
document.addEventListener("keydown", e => {{ if (e.key === "Escape") lb.classList.remove("open"); }});
</script>
</body></html>
"""
    index = board_dir / "index.html"
    index.write_text(page, encoding="utf-8")
    return index
