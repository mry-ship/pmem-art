#!/usr/bin/env python3
"""First-round batch only. Not a skill finish.

Each job writes r1.jpg. That is not a winner. Do not copy r1 to final.jpg
and do not put it on the showcase as 终稿 unless
`can_accept_winner(rounds, score)` is true (>= 9.5 or full 4 rounds).

After this script: each cell still needs converge generate/judge until
the gate passes. Check with:

    python pmem_art.py showcase-gate --html docs/showcase/homepage_rerun_1029/index.html

Does not overwrite the 10-28 page. Writes docs/showcase/homepage_rerun_1029/.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import types
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
if sys.platform == "win32" and "fcntl" not in sys.modules:
    sys.modules["fcntl"] = types.ModuleType("fcntl")

from skills_kit.prompt_scale import compose_style_first_prompt, get_converge_scale_profile  # noqa: E402

IMAGE_GEN = Path(r"C:\Users\ZhengLangPC\.cursor\skills\apikey-image\image_gen.py")
OLD = REPO / "docs" / "showcase" / "homepage_rerun_1028"
OUT = REPO / "docs" / "showcase" / "homepage_rerun_1029"
JOBS_JSON = REPO / "_tmp_hp_jobs.json"
WORKERS = 5
SIZE = {
    "9:16": "1024x1536",
    "3:4": "1024x1536",
    "4:3": "1536x1024",
    "16:9": "1536x1024",
    "1:1": "1024x1024",
}


def extra_jobs() -> list[dict]:
    c02 = "docs/showcase/homepage_rerun_1028/draw_matrix/c02/ref.jpg"
    c03 = "docs/showcase/homepage_rerun_1028/draw_matrix/c03/ref.jpg"
    rabbit = "docs/showcase/homepage_rerun_1028/v2/clone_rabbit/ref.jpg"
    expr = "docs/showcase/homepage_rerun_1028/v2/variant_expr/ref.jpg"
    return [
        {
            "id": "ui_royal",
            "skill": "ui",
            "out": "v2/ui_royal/portrait/r1.jpg",
            "old": "v2/ui_royal/portrait/final.jpg",
            "aspect_ratio": "9:16",
            "prompt": (
                "9:16 casual match-3 home screen, Royal Match quality. Butter-yellow greenhouse "
                "background: arch windows, plant shelves, red velvet sofa, tea set, gold watering can, "
                "lemon tree, blue rug. UI overlay: coin 2860, hearts, 01:12:05, stars 6, watering-can "
                "progress 120/500 x3, three round badges top-left, gold bell top-right, Garden 12 and "
                "Room 3, Home tab. Glazed candy buttons, champagne gold bevel, no readable garbage text, "
                "no neon, no hard cel. Soft studio light."
            ),
        },
        {
            "id": "icon_a_city",
            "skill": "icon.a",
            "out": "v2/icon_a/r1.jpg",
            "old": "v2/icon_a/final.jpg",
            "aspect_ratio": "1:1",
            "prompt": "1024 app icon, full-bleed square, no rounded-corner mask, no text. Indigo sky, one floating city plus moon disc inside 75 percent safe zone, tiny gold stars, tactile micro-bevel, no letters.",
        },
        {
            "id": "icon_a_coin",
            "skill": "icon.a",
            "out": "v2/icon_a2/r1.jpg",
            "old": "v2/icon_a2/final.jpg",
            "aspect_ratio": "1:1",
            "prompt": "1024 app icon, full-bleed square, no text. Celadon glaze gold coin, wet highlight stripe, 75 percent safe zone, no letters.",
        },
        {
            "id": "icon_a_forge",
            "skill": "icon.a",
            "out": "v2/icon_a3/r1.jpg",
            "old": "v2/icon_a3/final.jpg",
            "aspect_ratio": "1:1",
            "prompt": "1024 app icon, full-bleed square, no text. Hammer and anvil with ember glow, 75 percent safe zone, no letters.",
        },
        {
            "id": "icon_c_heal",
            "skill": "icon.c",
            "out": "v2/icon_c_set/heal.jpg",
            "old": "v2/icon_c_set/heal.jpg",
            "aspect_ratio": "1:1",
            "transparent": True,
            "prompt": "Game item icon, thick silhouette, studio light, vignette, no text. Red healing potion bottle, cork, readable glass, centered.",
        },
        {
            "id": "icon_c_mana",
            "skill": "icon.c",
            "out": "v2/icon_c_set/mana.jpg",
            "old": "v2/icon_c_set/mana.jpg",
            "aspect_ratio": "1:1",
            "transparent": True,
            "prompt": "Game item icon, thick silhouette, studio light, vignette, no text. Blue mana potion bottle, cork, centered.",
        },
        {
            "id": "icon_c_key",
            "skill": "icon.c",
            "out": "v2/icon_c_set/key.jpg",
            "old": "v2/icon_c_set/key.jpg",
            "aspect_ratio": "1:1",
            "transparent": True,
            "prompt": "Game item icon, thick silhouette, studio light, vignette, no text. Warm metal antique key, readable teeth, centered.",
        },
        {
            "id": "icon_c_ruby",
            "skill": "icon.c",
            "out": "v2/icon_c_set/ruby.jpg",
            "old": "v2/icon_c_set/ruby.jpg",
            "aspect_ratio": "1:1",
            "transparent": True,
            "prompt": "Game item icon, thick silhouette, studio light, vignette, no text. Faceted ruby gem, hard speculars, centered.",
        },
        {
            "id": "icon_c_scroll",
            "skill": "icon.c",
            "out": "v2/icon_c_set/scroll.jpg",
            "old": "v2/icon_c_set/scroll.jpg",
            "aspect_ratio": "1:1",
            "transparent": True,
            "prompt": "Game item icon, thick silhouette, studio light, vignette, no text. Rolled parchment with red wax seal, centered, no readable writing.",
        },
        {
            "id": "clone_kite",
            "skill": "clone",
            "out": "v2/clone/r1.jpg",
            "old": "v2/clone/final.jpg",
            "aspect_ratio": "4:3",
            "ref_image": c02,
            "prompt": "New subject, keep only oil-pastel paper tooth and blush air. Short-hair boy sitting on stone steps holding a paper kite roll. Crayon diagonal strokes, warm paper. Not the red-hoodie girl.",
        },
        {
            "id": "clone_rabbit",
            "skill": "clone",
            "out": "v2/clone_rabbit/r1.jpg",
            "old": "v2/clone_rabbit/final.jpg",
            "aspect_ratio": "1:1",
            "ref_image": rabbit,
            "prompt": "New subject, keep pastel line and blush air. White rabbit hugging a carrot, new composition, no cyber neon.",
        },
        {
            "id": "variant_light",
            "skill": "variant",
            "out": "v2/variant/r1.jpg",
            "old": "v2/variant/final.jpg",
            "aspect_ratio": "3:4",
            "ref_image": c03,
            "prompt": "Same sunlit window girl identity and camera. Strengthen hair translucency, skin SSS, dust motes, warm gold rim light. Do not change outfit, headphones, or cat clip.",
        },
        {
            "id": "variant_surprise",
            "skill": "variant",
            "out": "v2/variant_expr/r1.jpg",
            "old": "v2/variant_expr/final.jpg",
            "aspect_ratio": "3:4",
            "ref_image": expr,
            "prompt": "Same window girl identity, camera, hair, cat clip, headphones, white tee. ONLY change expression to surprised open mouth showing upper teeth.",
        },
        {
            "id": "variant_wink",
            "skill": "variant",
            "out": "v2/variant_wink/r1.jpg",
            "old": "v2/variant_wink/final.jpg",
            "aspect_ratio": "3:4",
            "ref_image": expr,
            "prompt": "Same window girl identity and camera. ONLY change expression to a playful wink. Keep cat clip and headphones.",
        },
        {
            "id": "variant_sleepy",
            "skill": "variant",
            "out": "v2/variant_sleepy/r1.jpg",
            "old": "v2/variant_sleepy/final.jpg",
            "aspect_ratio": "3:4",
            "ref_image": expr,
            "prompt": "Same window girl identity and camera. ONLY change expression to sleepy half-lidded eyes.",
        },
        {
            "id": "variant_angry",
            "skill": "variant",
            "out": "v2/variant_angry/r1.jpg",
            "old": "v2/variant_angry/final.jpg",
            "aspect_ratio": "3:4",
            "ref_image": expr,
            "prompt": "Same window girl identity and camera. ONLY change expression to a slight pout, mildly angry.",
        },
        *merge_jobs(),
    ]


def merge_jobs() -> list[dict]:
    potion = [
        ("L01", "empty cut-glass potion bottle, no cork, no liquid"),
        ("L02", "cut-glass potion bottle with cork stopper, still empty"),
        ("L03", "cut-glass potion bottle with cork, half filled with warm green healing liquid"),
        ("L04", "cut-glass potion bottle with cork, full green healing liquid"),
        ("L05", "full green potion with paper tag ring and leaf ornament on the neck"),
        ("L06", "full tagged potion sitting on a small warm-gold stand"),
    ]
    candy = [
        ("L01", "bare peach gummy candy, no wrapper"),
        ("L02", "peach gummy in clear candy wrapper"),
        ("L03", "wrapped peach candy with a small sticker"),
        ("L04", "wrapped sticker candy sitting in a paper cup"),
        ("L05", "paper-cup candy tied with a ribbon"),
        ("L06", "ribbon candy on a small serving tray"),
    ]
    jobs = []
    for code, desc in potion:
        jobs.append(
            {
                "id": f"potion_{code}",
                "skill": "merge",
                "out": f"v2/merge_potion_l16/{code}.jpg",
                "old": f"v2/merge_potion_l16/{code}.jpg",
                "aspect_ratio": "1:1",
                "prompt": (
                    f"One square product shot, single object centered, no face, no rank text. "
                    f"Cut glass plus warm gold. {desc}."
                ),
            }
        )
    for code, desc in candy:
        jobs.append(
            {
                "id": f"candy_{code}",
                "skill": "merge",
                "out": f"v2/merge_candy_l16/{code}.jpg",
                "old": f"v2/merge_candy_l16/{code}.jpg",
                "aspect_ratio": "1:1",
                "prompt": (
                    f"One square product shot, single object centered, no face, no rank text. "
                    f"Soft vinyl candy court style. {desc}."
                ),
            }
        )
    jobs.append(
        {
            "id": "merge_t5",
            "skill": "merge",
            "out": "v2/merge/r1.jpg",
            "old": "v2/merge/final.jpg",
            "aspect_ratio": "1:1",
            "prompt": "One square product shot, crystal-crown potion bottle, cut glass, warm gold crown cap, single object centered, no face, no rank text.",
        }
    )
    return jobs


def draw_jobs() -> list[dict]:
    rows = json.loads(JOBS_JSON.read_text(encoding="utf-8"))
    out = []
    for row in rows:
        cid, scale = row["id"].split("_", 1)
        prompt = compose_draw_prompt(row)
        out.append(
            {
                "id": row["id"],
                "skill": "draw",
                "scale": scale,
                "out": f"draw_matrix/{cid}/{scale}/r1.jpg",
                "old": f"draw_matrix/{cid}/{scale}/final.jpg",
                "aspect_ratio": row["aspect_ratio"],
                "ref_image": row["ref_image"],
                "prompt": prompt,
                "module": row.get("module") or "",
            }
        )
    return out


def compose_draw_prompt(row: dict) -> str:
    base = " | ".join(x for x in (row.get("ref_analysis"), row.get("goal"), row.get("recompose_dir")) if x)
    prof = get_converge_scale_profile(
        row["scale"],
        recompose_dir=row.get("recompose_dir") or "",
        goal=row.get("goal") or "",
        ref_image=row.get("ref_image") or "",
        module=row.get("module") or "",
    )
    return compose_style_first_prompt(base, prof)[:3500]


def run_one(job: dict) -> dict:
    dest = OUT / job["out"]
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = SIZE.get(job.get("aspect_ratio") or "1:1", "1024x1024")
    cmd = [sys.executable, str(IMAGE_GEN), "-o", str(dest), "--size", size, "--quality", "high"]
    if job.get("transparent"):
        cmd += ["--background", "transparent"]
    ref = job.get("ref_image") or ""
    if ref:
        src = REPO / ref if not Path(ref).is_absolute() else Path(ref)
        if src.is_file():
            cmd += ["--image", str(src)]
    cmd.append(job["prompt"])
    err = ""
    ok = False
    for attempt in range(1, 4):
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=420, encoding="utf-8", errors="replace")
            if proc.returncode == 0 and dest.is_file() and dest.stat().st_size > 1000:
                ok = True
                break
            err = (proc.stderr or proc.stdout or f"exit {proc.returncode}")[:400]
        except Exception as exc:  # noqa: BLE001
            err = f"{type(exc).__name__}: {exc}"[:400]
        print(f"  retry {attempt} {job['id']}: {err[:160]}", flush=True)
    print(f"{'OK' if ok else 'FAIL'} {job['id']} bytes={dest.stat().st_size if dest.is_file() else 0}", flush=True)
    return {
        "id": job["id"],
        "skill": job.get("skill") or "",
        "out": job["out"],
        "old": job.get("old") or "",
        "ok": ok,
        "error": err,
        "prompt": job["prompt"],
        "aspect_ratio": job.get("aspect_ratio") or "",
        "ref_image": ref,
    }


def copy_static() -> None:
    pairs = [
        ("draw_matrix/c01/ref.jpg", "draw_matrix/c01/ref.jpg"),
        ("draw_matrix/c02/ref.jpg", "draw_matrix/c02/ref.jpg"),
        ("draw_matrix/c03/ref.jpg", "draw_matrix/c03/ref.jpg"),
        ("draw_matrix/c04/ref.jpg", "draw_matrix/c04/ref.jpg"),
        ("v2/clone_rabbit/ref.jpg", "v2/clone_rabbit/ref.jpg"),
        ("v2/variant_expr/ref.jpg", "v2/variant_expr/ref.jpg"),
        ("v2/style_lock_b/ref1.jpg", "v2/style_lock_b/ref1.jpg"),
        ("v2/style_lock_b/ref2.jpg", "v2/style_lock_b/ref2.jpg"),
        ("v2/style_lock_b/final.jpg", "v2/style_lock_b/final.jpg"),
        ("v2/style_lock_c/ref1.jpg", "v2/style_lock_c/ref1.jpg"),
        ("v2/style_lock_c/ref2.jpg", "v2/style_lock_c/ref2.jpg"),
        ("v2/style_lock_c/final.jpg", "v2/style_lock_c/final.jpg"),
    ]
    for src, dst in pairs:
        s, d = OLD / src, OUT / dst
        if s.is_file():
            d.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, d)


def pair_img(old_rel: str, new_rel: str, old_cap: str, new_cap: str, cls: str = "") -> str:
    old_src = f"../homepage_rerun_1028/{old_rel}" if old_rel else ""
    new_ok = (OUT / new_rel).is_file() if new_rel else False
    old_fig = (
        f'<figure class="ref {cls}"><img src="{old_src}" alt="old" /><figcaption><strong>旧 · {old_cap}</strong></figcaption></figure>'
        if old_rel
        else "<figure class='pending'><figcaption>无旧图</figcaption></figure>"
    )
    if new_ok:
        new_fig = f'<figure class="pending {cls}"><img src="{new_rel}" alt="new" /><figcaption><strong>新 · {new_cap} · 第 1 轮未审图</strong>不能当终稿</figcaption></figure>'
    else:
        new_fig = f'<figure class="pending {cls}"><figcaption><strong>新 · {new_cap}</strong>未出图</figcaption></figure>'
    return f'<div class="pair">{old_fig}{new_fig}</div>'


def write_html(results: list[dict]) -> Path:
    by_id = {r["id"]: r for r in results}
    ok_n = sum(1 for r in results if r["ok"])
    fail = [r["id"] for r in results if not r["ok"]]

    def cell(jid: str, old: str, cap: str, cls: str = "") -> str:
        row = by_id.get(jid) or {}
        new = row.get("out") or ""
        status = "出图成功" if row.get("ok") else (row.get("error") or "未跑")[:80]
        return pair_img(old, new, cap, f"{cap} · {status}", cls)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>主页展陈对照 · 10-28 vs 10-29 并发重跑</title>
<style>
  :root {{ --bg:#0b0f19; --card:#111827; --line:#1e293b; --text:#f1f5f9; --muted:#94a3b8; --dim:#64748b; --accent:#38bdf8; --ok:#34d399; --warn:#fbbf24; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; color:var(--text); font:14px/1.55 "PingFang SC","Noto Sans SC",system-ui,sans-serif; background:var(--bg); }}
  a {{ color:var(--accent); }}
  .wrap {{ max-width:1200px; margin:0 auto; padding:28px 18px 72px; }}
  .hero {{ border:1px solid #312e81; border-radius:18px; padding:24px 26px; background:linear-gradient(135deg,#111827,#1e1b4b 55%,#0f172a); margin-bottom:22px; }}
  .hero h1 {{ margin:0 0 8px; font-size:26px; }}
  .hero p {{ margin:0; color:#cbd5e1; max-width:80ch; }}
  .pills {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:12px; }}
  .pill {{ font-size:12px; padding:4px 12px; border-radius:999px; border:1px solid rgba(255,255,255,.14); color:var(--muted); }}
  .pill.ok {{ color:var(--ok); border-color:rgba(52,211,153,.4); }}
  .pill.warn {{ color:var(--warn); border-color:rgba(251,191,36,.4); }}
  nav.toc {{ position:sticky; top:0; z-index:5; display:flex; flex-wrap:wrap; gap:8px; padding:10px 0 14px; background:rgba(11,15,25,.92); }}
  nav.toc a {{ font-size:12px; color:var(--muted); padding:4px 12px; border-radius:999px; text-decoration:none; }}
  section {{ border:1px solid var(--line); border-radius:16px; background:var(--card); padding:18px; margin-bottom:16px; }}
  section h2 {{ margin:0 0 6px; font-size:18px; }}
  .lead {{ color:var(--muted); margin:0 0 14px; font-size:13px; }}
  .case-title {{ margin:18px 0 8px; font-size:15px; color:#e2e8f0; }}
  .pair {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:10px; }}
  .row4 {{ display:grid; grid-template-columns:1fr 1fr; gap:10px; }}
  figure {{ margin:0; border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#0b1220; }}
  figure.ref {{ border-color:rgba(56,189,248,.45); }}
  figure.win {{ border-color:rgba(251,191,36,.55); }}
  figure.pending {{ opacity:.55; border-style:dashed; min-height:80px; }}
  figure img {{ display:block; width:100%; aspect-ratio:3/4; object-fit:cover; }}
  figure.wide img {{ aspect-ratio:4/3; }}
  figure.sq img {{ aspect-ratio:1; }}
  figure.port img {{ aspect-ratio:9/16; object-fit:contain; }}
  #icon figure img, #merge figure img {{ aspect-ratio:1/1; object-fit:contain; }}
  figcaption {{ padding:8px 10px; font-size:12px; color:var(--muted); border-top:1px solid var(--line); }}
  figcaption strong {{ display:block; color:var(--text); }}
  footer {{ text-align:center; color:var(--dim); font-size:12px; margin-top:20px; }}
  @media (max-width:900px) {{ .pair,.row4 {{ grid-template-columns:1fr; }} }}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <h1>主页展陈对照 · 10-28 旧稿 vs 10-29 并发重跑</h1>
    <p>
      同范围重跑，不覆盖旧页。左栏是
      <a href="../homepage_rerun_1028/index.html">homepage_rerun_1028</a>
      终稿，右栏是本趟并发新图（第 1 轮）。锁风格与提示词不生图，沿用旧卡。
      本趟出图 {ok_n}/{len(results)}。
    </p>
    <div class="pills">
      <span class="pill ok">并发 workers={WORKERS}</span>
      <span class="pill ok">gpt-image-2.5-sunburst</span>
      <span class="pill {'ok' if not fail else 'warn'}">{'全部成功' if not fail else '失败: ' + ', '.join(fail[:12])}</span>
    </div>
  </header>
  <nav class="toc">
    <a href="#matrix">四案例×四档</a>
    <a href="#ui">界面</a>
    <a href="#icon">图标</a>
    <a href="#draw-extra">克隆/变体</a>
    <a href="#merge">合成梯</a>
    <a href="#style">锁风格</a>
  </nav>

  <section id="matrix">
    <h2>draw · 四案例 × 四档</h2>
    <p class="lead">每档左旧右新。垫的仍是旧页原图。</p>
    <div class="case-title">案例 01 · 仙侠不夜城</div>
    {cell('c01_low','draw_matrix/c01/low/r4.jpg','low', '')}
    {cell('c01_medium','draw_matrix/c01/medium/r4.jpg','medium')}
    {cell('c01_high','draw_matrix/c01/high/r4.jpg','high')}
    {cell('c01_recompose','draw_matrix/c01/recompose/r4.jpg','recompose')}
    <div class="case-title">案例 02 · 粉彩速写少女</div>
    {cell('c02_low','draw_matrix/c02/low/r3.jpg','low','wide')}
    {cell('c02_medium','draw_matrix/c02/medium/r4.jpg','medium','wide')}
    {cell('c02_high','draw_matrix/c02/high/r4.jpg','high','wide')}
    {cell('c02_recompose','draw_matrix/c02/recompose/r4.jpg','recompose','wide')}
    <div class="case-title">案例 03 · 窗边日光胸像</div>
    {cell('c03_low','draw_matrix/c03/low/r4.jpg','low')}
    {cell('c03_medium','draw_matrix/c03/medium/r4.jpg','medium')}
    {cell('c03_high','draw_matrix/c03/high/r3.jpg','high')}
    {cell('c03_recompose','draw_matrix/c03/recompose/r3.jpg','recompose')}
    <div class="case-title">案例 04 · 天井石院</div>
    {cell('c04_low','draw_matrix/c04/low/r4.jpg','low','wide')}
    {cell('c04_medium','draw_matrix/c04/medium/r4.jpg','medium','wide')}
    {cell('c04_high','draw_matrix/c04/high/r4.jpg','high','wide')}
    {cell('c04_recompose','draw_matrix/c04/recompose/r4.jpg','recompose','wide')}
  </section>

  <section id="ui">
    <h2>界面</h2>
    {cell('ui_royal','v2/ui_royal/portrait/final.jpg','Royal Match 花房主界面','port')}
  </section>

  <section id="icon">
    <h2>图标 A / C</h2>
    <div class="case-title">Mode A</div>
    {cell('icon_a_city','v2/icon_a/final.jpg','浮城','sq')}
    {cell('icon_a_coin','v2/icon_a2/final.jpg','青瓷金','sq')}
    {cell('icon_a_forge','v2/icon_a3/final.jpg','锻炉','sq')}
    <div class="case-title">Mode C</div>
    {cell('icon_c_heal','v2/icon_c_set/heal.jpg','治疗药','sq')}
    {cell('icon_c_mana','v2/icon_c_set/mana.jpg','法力药','sq')}
    {cell('icon_c_key','v2/icon_c_set/key.jpg','钥匙','sq')}
    {cell('icon_c_ruby','v2/icon_c_set/ruby.jpg','宝石','sq')}
    {cell('icon_c_scroll','v2/icon_c_set/scroll.jpg','卷轴','sq')}
  </section>

  <section id="draw-extra">
    <h2>克隆 / 变体</h2>
    {cell('clone_kite','v2/clone/final.jpg','克隆 · 少年风筝','wide')}
    {cell('clone_rabbit','v2/clone_rabbit/final.jpg','克隆 · 白兔')}
    {cell('variant_light','v2/variant/final.jpg','变体 · 光影加码')}
    {cell('variant_surprise','v2/variant_expr/final.jpg','变体 · 惊喜')}
    {cell('variant_wink','v2/variant_wink/final.jpg','变体 · 眨眼')}
    {cell('variant_sleepy','v2/variant_sleepy/final.jpg','变体 · 困倦')}
    {cell('variant_angry','v2/variant_angry/final.jpg','变体 · 微怒')}
  </section>

  <section id="merge">
    <h2>合成梯</h2>
    <div class="case-title">青金治疗药 L1–L6</div>
    {cell('potion_L01','v2/merge_potion_l16/L01.jpg','L1 空瓶','sq')}
    {cell('potion_L02','v2/merge_potion_l16/L02.jpg','L2 塞','sq')}
    {cell('potion_L03','v2/merge_potion_l16/L03.jpg','L3 半药','sq')}
    {cell('potion_L04','v2/merge_potion_l16/L04.jpg','L4 满药','sq')}
    {cell('potion_L05','v2/merge_potion_l16/L05.jpg','L5 签环','sq')}
    {cell('potion_L06','v2/merge_potion_l16/L06.jpg','L6 金托','sq')}
    <div class="case-title">蜜桃糖 L1–L6</div>
    {cell('candy_L01','v2/merge_candy_l16/L01.jpg','L1 裸糖','sq')}
    {cell('candy_L02','v2/merge_candy_l16/L02.jpg','L2 糖纸','sq')}
    {cell('candy_L03','v2/merge_candy_l16/L03.jpg','L3 贴纸','sq')}
    {cell('candy_L04','v2/merge_candy_l16/L04.jpg','L4 纸托','sq')}
    {cell('candy_L05','v2/merge_candy_l16/L05.jpg','L5 丝带','sq')}
    {cell('candy_L06','v2/merge_candy_l16/L06.jpg','L6 托盘','sq')}
    {cell('merge_t5','v2/merge/final.jpg','T5 晶冠瓶','sq')}
  </section>

  <section id="style">
    <h2>锁风格 · 不生图</h2>
    <p class="lead">沿用旧样张与锁定卡，本趟不重画。</p>
    <div class="pair">
      <figure class="ref land"><img src="v2/style_lock_b/final.jpg" alt="ink" /><figcaption><strong>Ink Wash Sage</strong></figcaption></figure>
      <figure class="ref land"><img src="v2/style_lock_c/final.jpg" alt="cel" /><figcaption><strong>Bold Cel</strong></figcaption></figure>
    </div>
  </section>
  <footer>新页 docs/showcase/homepage_rerun_1029/compare.html · 旧页不覆盖</footer>
</div>
</body>
</html>
"""
    path = OUT / "compare.html"
    path.write_text(html, encoding="utf-8")
    return path


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    copy_static()
    jobs = draw_jobs() + extra_jobs()
    print(f"jobs={len(jobs)} workers={WORKERS}", flush=True)
    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futs = {pool.submit(run_one, job): job for job in jobs}
        for fut in as_completed(futs):
            results.append(fut.result())
    results.sort(key=lambda r: r["id"])
    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    html = write_html(results)
    ok = sum(1 for r in results if r["ok"])
    print(f"done {ok}/{len(results)} html={html}", flush=True)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
