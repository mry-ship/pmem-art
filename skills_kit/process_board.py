"""Process board artifacts written at converge finish.

Primary deliverable for artists: a single composited JPG「过程图」with scores
and defects. HTML remains a silent sidecar for showcase-gate compatibility.
"""
from __future__ import annotations

import html
import shutil
import textwrap
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
    if score >= 9.5:
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


def _reference_images(root: Path, sess: dict[str, Any]) -> list[Path]:
    """Every comparison still, in the order the session recorded them. ref_image alone drops the others."""
    raw: list[str] = []
    for key in ("default_reference_image_paths", "reference_image_paths"):
        val = sess.get(key) or []
        if isinstance(val, str):
            raw.extend(part.strip() for part in val.split(",") if part.strip())
        else:
            raw.extend(str(part).strip() for part in val if str(part).strip())
    if sess.get("ref_image"):
        raw.append(str(sess.get("ref_image")))
    found: list[Path] = []
    seen: set[str] = set()
    for item in raw:
        path = _find_image(root, item)
        if path is None:
            continue
        key = str(path.resolve()).lower()
        if key in seen:
            continue
        seen.add(key)
        found.append(path)
    return found


def _board_dir(root: Path, sess: dict[str, Any]) -> Path:
    session_id = str(sess.get("session_id") or "session")
    safe = "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in session_id) or "session"
    return root / ".memory-art" / "converge" / "boards" / safe


def _threshold(sess: dict[str, Any]) -> float:
    try:
        return float(sess.get("accept_threshold") or sess.get("threshold") or 9.5)
    except (TypeError, ValueError):
        return 9.5


def _summary_text(sess: dict[str, Any], winner: dict[str, Any] | None, line: float) -> str:
    badge = str(sess.get("convergence_badge") or "").strip()
    if winner:
        sc_win = _score(winner)
        mark = "到线。" if sc_win is not None and sc_win >= line else f"未到 {line:.2f}。"
        total = "" if sc_win is None else f"{sc_win:.2f}"
        end = (
            f"胜出第 {int(winner.get('round') or 0)} 轮，总分 {total}。{mark}"
            f"{winner.get('defects') or '这一轮没有留下不足。'}"
        )
    else:
        end = "还没有胜出轮。"
    if badge:
        end = f"{badge}。{end}"
    return end


def _clip(text: Any, n: int = 72) -> str:
    s = " ".join(str(text or "").split())
    if len(s) <= n:
        return s
    return s[: max(0, n - 1)] + "…"


def _load_font(size: int):
    from PIL import ImageFont

    candidates = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "/System/Library/Fonts/PingFang.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def _fit_thumb(img, box: tuple[int, int]):
    from PIL import Image

    tw, th = box
    src = img.convert("RGB")
    src.thumbnail((tw, th), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (tw, th), (18, 24, 32))
    x = (tw - src.width) // 2
    y = (th - src.height) // 2
    canvas.paste(src, (x, y))
    return canvas


def write_process_sheet(
    root: Path,
    sess: dict[str, Any],
    *,
    winner: dict[str, Any] | None = None,
    board_dir: Path | None = None,
) -> Path:
    """Composite a single JPG process sheet with scores / defects / winner frame."""
    try:
        from PIL import Image, ImageDraw
    except ImportError as exc:
        raise RuntimeError("需要 Pillow：pip install pillow") from exc

    root = Path(root)
    out_dir = Path(board_dir) if board_dir is not None else _board_dir(root, sess)
    out_dir.mkdir(parents=True, exist_ok=True)
    img_dir = out_dir / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    win_round = int((winner or sess.get("winner") or {}).get("round") or 0)
    rounds = list(sess.get("rounds") or [])
    line = _threshold(sess)
    goal = str(sess.get("goal") or sess.get("session_id") or "过程图")
    summary = _summary_text(sess, winner, line)

    # Layout: header + grid (up to 4 cells) + footer
    n = max(1, len(rounds))
    cols = 2 if n >= 2 else 1
    rows = (n + cols - 1) // cols
    cell_w, cell_h = 420, 520
    thumb_w, thumb_h = 380, 300
    pad = 16
    header_h = 92
    footer_h = 110
    sheet_w = pad + cols * (cell_w + pad)
    sheet_h = header_h + pad + rows * (cell_h + pad) + footer_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), (27, 36, 48))
    draw = ImageDraw.Draw(sheet)
    font_title = _load_font(22)
    font_h = _load_font(18)
    font_body = _load_font(14)
    font_small = _load_font(12)

    # Header
    draw.rectangle((0, 0, sheet_w, header_h), fill=(36, 49, 64))
    title_lines = textwrap.wrap(_clip(goal, 80), width=42)[:2] or ["过程图"]
    y = 14
    for tl in title_lines:
        draw.text((pad, y), tl, fill=(232, 238, 246), font=font_title)
        y += 26
    sc_win = _score(winner or {}) if winner else None
    status = (
        f"过线 · 胜出第 {win_round} 轮 · {sc_win:.2f}"
        if sc_win is not None and sc_win >= line
        else (
            f"未过线 · 胜出第 {win_round} 轮 · {sc_win:.2f}"
            if sc_win is not None
            else "过程图"
        )
    )
    draw.text((pad, header_h - 28), status, fill=(143, 209, 143) if (sc_win is not None and sc_win >= line) else (230, 195, 106), font=font_h)

    if not rounds:
        draw.text((pad, header_h + 24), "还没有出图轮。", fill=(201, 208, 220), font=font_body)
    else:
        for i, row in enumerate(rounds):
            r = int(row.get("round") or (i + 1))
            col = i % cols
            row_i = i // cols
            x0 = pad + col * (cell_w + pad)
            y0 = header_h + pad + row_i * (cell_h + pad)
            is_win = r == win_round
            border = (232, 93, 76) if is_win else (51, 65, 85)
            fill = (45, 32, 32) if is_win else (36, 49, 64)
            draw.rounded_rectangle(
                (x0, y0, x0 + cell_w, y0 + cell_h),
                radius=10,
                fill=fill,
                outline=border,
                width=3 if is_win else 1,
            )
            sc = _score(row)
            sc_txt = "待审" if sc is None else f"{sc:.2f}"
            caption = f"第 {r} 轮 · {sc_txt}" + ("  ★胜出" if is_win else "")
            color = (143, 209, 143) if (sc is not None and sc >= 9.5) else ((230, 195, 106) if (sc is not None and sc >= 8.5) else (224, 160, 160))
            draw.text((x0 + 12, y0 + 10), caption, fill=color, font=font_h)
            dims = _clip(row.get("dims") or "未记六维", 56)
            draw.text((x0 + 12, y0 + 36), dims, fill=(197, 208, 220), font=font_small)

            src = _find_image(root, str(row.get("image") or ""))
            thumb_box = (x0 + 20, y0 + 58, x0 + 20 + thumb_w, y0 + 58 + thumb_h)
            if src:
                try:
                    with Image.open(src) as im:
                        thumb = _fit_thumb(im, (thumb_w, thumb_h))
                    sheet.paste(thumb, (thumb_box[0], thumb_box[1]))
                    # Also keep a copy under images/ for HTML sidecar
                    _copy_image(src, img_dir, f"r{r}")
                except OSError:
                    draw.rectangle(thumb_box, fill=(18, 24, 32))
                    draw.text((thumb_box[0] + 12, thumb_box[1] + 12), "读图失败", fill=(224, 160, 160), font=font_body)
            else:
                draw.rectangle(thumb_box, fill=(18, 24, 32))
                draw.text((thumb_box[0] + 12, thumb_box[1] + 12), "缺图", fill=(224, 160, 160), font=font_body)

            bullets: list[str] = []
            if row.get("defects"):
                bullets.append(f"不足：{_clip(row.get('defects'), 90)}")
            if row.get("next_fix"):
                bullets.append(f"改点：{_clip(row.get('next_fix'), 70)}")
            if not bullets and row.get("strengths"):
                bullets.append(f"亮点：{_clip(row.get('strengths'), 90)}")
            ty = y0 + 58 + thumb_h + 10
            for b in bullets[:2]:
                for wl in textwrap.wrap(b, width=28)[:2]:
                    draw.text((x0 + 12, ty), wl, fill=(213, 222, 234), font=font_small)
                    ty += 16

    # Footer summary
    fy = sheet_h - footer_h
    draw.rectangle((0, fy, sheet_w, sheet_h), fill=(36, 49, 64))
    draw.text((pad, fy + 12), "总结", fill=(232, 238, 246), font=font_h)
    sy = fy + 40
    for wl in textwrap.wrap(_clip(summary, 160), width=70)[:3]:
        draw.text((pad, sy), wl, fill=(213, 222, 234), font=font_body)
        sy += 20

    out = out_dir / "process_sheet.jpg"
    sheet.save(out, format="JPEG", quality=90, optimize=True)
    return out


def format_rounds_click_table(
    root: Path,
    sess: dict[str, Any],
    *,
    winner: dict[str, Any] | None = None,
    board_dir: Path | None = None,
) -> str:
    """Markdown table: 轮次 × 分数 × 可点开单图路径（相对仓库根）。"""
    root = Path(root)
    win_round = int((winner or sess.get("winner") or {}).get("round") or 0)
    out_dir = Path(board_dir) if board_dir is not None else _board_dir(root, sess)
    lines = [
        "### 轮次单图表（点路径看大图）",
        "",
        "| 轮次 | 分数 | 可点图 |",
        "| --- | --- | --- |",
    ]
    rounds = list(sess.get("rounds") or [])
    if not rounds:
        lines.append("| — | — | 还没有出图轮 |")
        return "\n".join(lines)

    for row in rounds:
        rn = int(row.get("round") or 0)
        sc = _score(row)
        sc_txt = "待审" if sc is None else f"{sc:.2f}"
        mark = " ★胜出" if rn == win_round else ""
        # Prefer board copy (stable under boards/.../images/), else session image.
        board_copy = None
        if out_dir.is_dir():
            for cand in (out_dir / "images").glob(f"r{rn}.*"):
                board_copy = cand
                break
        src = board_copy or _find_image(root, str(row.get("image") or ""))
        if src is None:
            link = "(缺图)"
        else:
            try:
                rel = src.resolve().relative_to(root.resolve()).as_posix()
            except ValueError:
                rel = src.as_posix()
            link = f"[第{rn}轮]({rel})"
        lines.append(f"| 第 {rn} 轮{mark} | {sc_txt} | {link} |")
    return "\n".join(lines)


def write_rounds_table(
    root: Path,
    sess: dict[str, Any],
    *,
    winner: dict[str, Any] | None = None,
    board_dir: Path | None = None,
) -> Path:
    """Write rounds.md next to process_sheet — clickable per-round table."""
    root = Path(root)
    out_dir = Path(board_dir) if board_dir is not None else _board_dir(root, sess)
    out_dir.mkdir(parents=True, exist_ok=True)
    body = format_rounds_click_table(root, sess, winner=winner, board_dir=out_dir)
    # Also embed relative thumbs for local preview of rounds.md
    extra = ["", "预览（同目录 images/）：", ""]
    win_round = int((winner or sess.get("winner") or {}).get("round") or 0)
    for row in list(sess.get("rounds") or []):
        rn = int(row.get("round") or 0)
        mark = " ★胜出" if rn == win_round else ""
        hits = list((out_dir / "images").glob(f"r{rn}.*")) if (out_dir / "images").is_dir() else []
        if hits:
            extra.append(f"- 第 {rn} 轮{mark}: ![](images/{hits[0].name})")
        else:
            extra.append(f"- 第 {rn} 轮{mark}: (缺图)")
    path = out_dir / "rounds.md"
    path.write_text(body + "\n" + "\n".join(extra) + "\n", encoding="utf-8")
    return path


def write_process_board(root: Path, sess: dict[str, Any], *, winner: dict[str, Any] | None = None) -> Path:
    """Write HTML sidecar + process sheet. Returns the HTML path (legacy callers).

    Prefer ``write_process_artifacts`` for both paths.
    """
    arts = write_process_artifacts(root, sess, winner=winner)
    return arts["board"]


def write_process_artifacts(
    root: Path,
    sess: dict[str, Any],
    *,
    winner: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Write process_sheet.jpg + rounds.md (click table) + index.html sidecar."""
    root = Path(root)
    board_dir = _board_dir(root, sess)
    img_dir = board_dir / "images"
    if img_dir.exists():
        shutil.rmtree(img_dir)
    img_dir.mkdir(parents=True, exist_ok=True)

    sheet_path = write_process_sheet(root, sess, winner=winner, board_dir=board_dir)

    win_round = int((winner or sess.get("winner") or {}).get("round") or 0)
    rounds = list(sess.get("rounds") or [])
    discussions = list(sess.get("discussions") or [])
    ref_paths = _reference_images(root, sess)
    ref_names = [_copy_image(path, img_dir, f"ref{i}") for i, path in enumerate(ref_paths, start=1)]

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
            f'<span class="dims">{_esc(row.get("dims") or "未记六维")}</span></figcaption>'
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
        title = "合理性闸 · 修订提示词" if note.get("kind") == "reasonableness" else f"论述第 {n} 稿"
        talk_cards.append(
            f'<article class="card talk"><h3>{_esc(title)}</h3>'
            f'<pre>{body}</pre><ul>{lis}</ul></article>'
        )

    line = _threshold(sess)
    end = _esc(_summary_text(sess, winner, line))
    session_id = str(sess.get("session_id") or "session")
    goal = _esc(sess.get("goal") or session_id)
    ref_block = ""
    if ref_names or sess.get("ref_analysis"):
        ref_cards = []
        for i, name in enumerate(ref_names, start=1):
            label = f"图{i}" if len(ref_names) > 1 else "参考图"
            ref_cards.append(
                f'<figure class="card ref"><figcaption><b>{label}</b></figcaption>'
                f'<button type="button" class="shot" data-full="images/{_esc(name)}">'
                f'<img src="images/{_esc(name)}" alt="{label}"></button></figure>'
            )
        note = f'<p class="note">{_esc(sess.get("ref_analysis") or "")}</p>' if sess.get("ref_analysis") else ""
        ref_block = (
            f'<section><h2>参考图分析</h2>{note}<div class="row">'
            f'{"".join(ref_cards)}</div></section>'
        )
    talk_block = ""
    if talk_cards:
        talk_block = f'<section><h2>论述过程</h2><div class="row">{"".join(talk_cards)}</div></section>'
    rounds_block = (
        f'<section><h2>出图过程</h2><div class="row">{"".join(cards) or "<p>还没有出图轮。</p>"}</div></section>'
    )
    sheet_rel = "process_sheet.jpg"

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
<p class="note">主交件是过程图 <code>{sheet_rel}</code>（对话里直接看）。本页是旁路：点图片看大图；红框是胜出轮。</p>
</header>
<section><h2>过程图</h2><p class="note"><a href="{sheet_rel}">{sheet_rel}</a></p>
<figure class="card"><img src="{sheet_rel}" alt="过程图"></figure></section>
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
    rounds_path = write_rounds_table(root, sess, winner=winner, board_dir=board_dir)
    return {"sheet": sheet_path, "board": index, "rounds": rounds_path}
