# -*- coding: utf-8 -*-
"""Game Art Layer Decomposer MVP: crop → AI alpha → original RGB → full-canvas layers → compose → validate → HTML."""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
ORIG = ROOT / "Original" / "Original.png"
MANIFEST = ROOT / "Manifest" / "layer_manifest.json"
LAYERS = ROOT / "Layers"
WORK = ROOT / "_work"
CROPS = WORK / "crops"
AI = WORK / "ai"
MASKS = WORK / "masks"
RECON = ROOT / "Reconstructed"
VAL = ROOT / "Validation"


def load_manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def save_manifest(m):
    MANIFEST.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


def export_crops(m):
    CROPS.mkdir(parents=True, exist_ok=True)
    im = Image.open(ORIG).convert("RGBA")
    W, H = im.size
    meta = {}
    for layer in m["layers"]:
        x, y, w, h = layer["bbox"]
        pad = 12 if layer["id"] != "background" else 0
        L = max(0, x - pad)
        T = max(0, y - pad)
        R = min(W, x + w + pad)
        B = min(H, y + h + pad)
        crop = im.crop((L, T, R, B))
        # upscale for AI quality
        scale = 3 if max(crop.size) < 400 else 2
        up = crop.resize((crop.size[0] * scale, crop.size[1] * scale), Image.Resampling.LANCZOS)
        out = CROPS / f"{layer['id']}.png"
        up.save(out)
        meta[layer["id"]] = {
            "L": L, "T": T, "R": R, "B": B,
            "cw": R - L, "ch": B - T,
            "scale": scale,
            "crop_file": str(out),
            "up_size": list(up.size),
        }
        print(f"crop {layer['id']}: {out.name} {up.size} from ({L},{T})-({R},{B})")
    (WORK / "crops_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return meta


def extract_alpha(ai_rgba: Image.Image) -> Image.Image:
    """Prefer real alpha; fall back to near-black/white chroma key."""
    ai = ai_rgba.convert("RGBA")
    a = np.array(ai)
    alpha = a[:, :, 3].astype(np.float32)
    if alpha.mean() < 250 and (alpha < 250).mean() > 0.02:
        return Image.fromarray(alpha.astype(np.uint8), "L")
    rgb = a[:, :, :3].astype(np.float32)
    # black / dark bg
    dark = rgb.mean(axis=2)
    # white / checker-ish bg
    bright = rgb.min(axis=2)
    mask = np.ones_like(dark) * 255
    mask[dark < 18] = 0
    mask[bright > 245] = 0
    # soft edge
    mimg = Image.fromarray(mask.astype(np.uint8), "L")
    mimg = mimg.filter(ImageFilter.GaussianBlur(1.2))
    return mimg


def align_mask_to_crop(ai: Image.Image, crop_rgb: Image.Image) -> Image.Image:
    """Resize AI alpha to crop size; optional shift search on luminance."""
    alpha = extract_alpha(ai)
    cw, ch = crop_rgb.size
    alpha = alpha.resize((cw, ch), Image.Resampling.LANCZOS)
    # refine: search small shifts maximizing overlap of AI opaque vs crop edge energy
    a = np.array(alpha).astype(np.float32) / 255.0
    g = np.array(crop_rgb.convert("L")).astype(np.float32)
    # gradient magnitude as edge cue
    gy, gx = np.gradient(g)
    edge = np.hypot(gx, gy)
    edge = edge / (edge.max() + 1e-6)
    best = (0, 0, -1.0)
    for dy in range(-6, 7):
        for dx in range(-6, 7):
            shifted = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
            score = float((shifted * edge).sum())
            if score > best[2]:
                best = (dx, dy, score)
    dx, dy, _ = best
    if dx or dy:
        a = np.roll(np.roll(a, dy, axis=0), dx, axis=1)
    # threshold soft
    a = np.clip(a * 1.05, 0, 1)
    return Image.fromarray((a * 255).astype(np.uint8), "L")


def recover_layer(layer_id: str, meta: dict, needs_inpaint: bool) -> Image.Image:
    """Original RGB + AI alpha on full canvas. For inpaint layers, allow AI RGB in hole regions."""
    m = meta[layer_id]
    crop = Image.open(CROPS / f"{layer_id}.png").convert("RGBA")
    # downscale crop back to canvas crop size
    crop_nat = crop.resize((m["cw"], m["ch"]), Image.Resampling.LANCZOS)
    ai_path = AI / f"{layer_id}.png"
    if not ai_path.exists():
        raise FileNotFoundError(ai_path)
    ai = Image.open(ai_path).convert("RGBA")
    # map AI onto natural crop size
    ai_nat = ai.resize((m["cw"], m["ch"]), Image.Resampling.LANCZOS)
    alpha = align_mask_to_crop(ai_nat, crop_nat.convert("RGB"))
    MASKS.mkdir(parents=True, exist_ok=True)
    alpha.save(MASKS / f"{layer_id}_alpha.png")

    orig_rgb = np.array(crop_nat.convert("RGB"))
    ai_rgb = np.array(ai_nat.convert("RGB"))
    a = np.array(alpha).astype(np.float32) / 255.0
    a3 = a[:, :, None]

    if needs_inpaint:
        # where AI opaque but original under mask is likely occluder (high RGB diff), keep AI
        diff = np.abs(orig_rgb.astype(np.float32) - ai_rgb.astype(np.float32)).mean(axis=2)
        use_ai = (a > 0.35) & (diff > 28)
        use_ai3 = use_ai[:, :, None]
        rgb = np.where(use_ai3, ai_rgb, orig_rgb)
    else:
        rgb = orig_rgb

    out_crop = np.dstack([rgb, (a * 255).astype(np.uint8)])
    out_crop_im = Image.fromarray(out_crop, "RGBA")

    # edge decontaminate: shrink alpha 1px then blur
    a_img = out_crop_im.getchannel("A")
    a_img = a_img.point(lambda v: 0 if v < 16 else v)
    a_img = a_img.filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.6))
    out_crop_im.putalpha(a_img)

    canvas = Image.new("RGBA", (409, 1024), (0, 0, 0, 0))
    canvas.paste(out_crop_im, (m["L"], m["T"]), out_crop_im)
    return canvas


def recover_background(meta: dict, mdoc: dict) -> Image.Image:
    """Full-canvas background: start from AI bg, paste original sky/ground outside object unions when similar."""
    ai_path = AI / "background.png"
    orig = Image.open(ORIG).convert("RGBA").resize((409, 1024), Image.Resampling.LANCZOS)
    if ai_path.exists():
        ai = Image.open(ai_path).convert("RGBA").resize((409, 1024), Image.Resampling.LANCZOS)
    else:
        ai = orig.copy()

    # union of foreground masks if available
    union = np.zeros((1024, 409), dtype=np.float32)
    for layer in mdoc["layers"]:
        if layer["id"] == "background":
            continue
        mp = MASKS / f"{layer['id']}_alpha.png"
        if not mp.exists():
            continue
        mm = meta[layer["id"]]
        a = np.array(Image.open(mp).convert("L")).astype(np.float32) / 255.0
        tile = np.zeros_like(union)
        tile[mm["T"]:mm["T"] + mm["ch"], mm["L"]:mm["L"] + mm["cw"]] = np.maximum(
            tile[mm["T"]:mm["T"] + mm["ch"], mm["L"]:mm["L"] + mm["cw"]], a
        )
        union = np.maximum(union, tile)

    o = np.array(orig.convert("RGB")).astype(np.float32)
    aimg = np.array(ai.convert("RGB")).astype(np.float32)
    # prefer original outside foreground; inside use AI inpaint
    w = np.clip(union, 0, 1)[:, :, None]
    rgb = o * (1 - w) + aimg * w
    # where no AI difference and no mask, keep original
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    return out


def compose(mdoc):
    canvas = Image.new("RGBA", (409, 1024), (0, 0, 0, 0))
    for layer in sorted(mdoc["layers"], key=lambda x: x["z_index"]):
        p = ROOT / layer["file"]
        if not p.exists():
            print("MISSING", p)
            continue
        im = Image.open(p).convert("RGBA")
        if im.size != (409, 1024):
            im = im.resize((409, 1024), Image.Resampling.LANCZOS)
        canvas = Image.alpha_composite(canvas, im)
    RECON.mkdir(parents=True, exist_ok=True)
    canvas.save(RECON / "Final.png")
    orig = Image.open(ORIG).convert("RGBA")
    overlay = Image.blend(orig, canvas, 0.5)
    overlay.save(RECON / "Final_Overlay.png")
    return canvas


def validate(final: Image.Image):
    VAL.mkdir(parents=True, exist_ok=True)
    orig = np.array(Image.open(ORIG).convert("RGB")).astype(np.float32)
    rec = np.array(final.convert("RGB").resize((409, 1024))).astype(np.float32)
    diff = np.abs(orig - rec)
    mae = float(diff.mean())
    mse = float(((orig - rec) ** 2).mean())
    psnr = 99.0 if mse < 1e-9 else float(20 * math.log10(255.0 / math.sqrt(mse)))
    # simple SSIM-ish on luminance
    o = orig.mean(axis=2)
    r = rec.mean(axis=2)
    mu_o, mu_r = o.mean(), r.mean()
    sig_o, sig_r = o.var(), r.var()
    sig_or = ((o - mu_o) * (r - mu_r)).mean()
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    ssim = float(((2 * mu_o * mu_r + c1) * (2 * sig_or + c2)) /
                 ((mu_o ** 2 + mu_r ** 2 + c1) * (sig_o + sig_r + c2)))
    heat = (diff.mean(axis=2) / max(diff.mean(axis=2).max(), 1e-6) * 255).astype(np.uint8)
    heat_rgb = np.stack([heat, (255 - heat) // 2, 40 * np.ones_like(heat)], axis=2)
    Image.fromarray(heat_rgb).save(VAL / "Difference.png")
    board = Image.new("RGB", (409 * 3 + 20, 1024), (24, 28, 34))
    board.paste(Image.open(ORIG).convert("RGB"), (0, 0))
    board.paste(final.convert("RGB"), (409 + 10, 0))
    board.paste(Image.open(RECON / "Final_Overlay.png").convert("RGB"), (409 * 2 + 20, 0))
    board.save(VAL / "Overlay.png")
    report = {
        "mae": round(mae, 3),
        "psnr": round(psnr, 3),
        "ssim_luma": round(ssim, 4),
        "note": "重建贴原指标；单层干净度需另目视（CleanSliceGate）",
    }
    (VAL / "Report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("VALIDATION", report)
    return report


def emit_html(mdoc, report):
    layers_js = []
    for layer in sorted(mdoc["layers"], key=lambda x: x["z_index"]):
        layers_js.append({
            "id": layer["id"],
            "name": f"{layer['z_index']:02d} {layer['name']}",
            "file": layer["file"].replace("Layers/", "Layers/"),
            "note": layer.get("prompt_focus", "")[:80],
        })
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>农场原画 · 图层拆解叠加</title>
<style>
  :root {{ --bg:#121820; --panel:#1c2633; --line:#314255; --text:#e8eef6; --muted:#93a4b8; --accent:#5bbcff; }}
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;color:var(--text);background:radial-gradient(1200px 600px at 20% -10%,#243247 0%,var(--bg) 55%);font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}}
  .wrap{{max-width:1240px;margin:0 auto;padding:20px 18px 40px;display:grid;grid-template-columns:minmax(300px,460px) 1fr;gap:22px}}
  @media (max-width:900px){{.wrap{{grid-template-columns:1fr}}}}
  h1{{font-size:20px;margin:0 0 6px;font-weight:650}}
  .sub{{color:var(--muted);font-size:13px;line-height:1.5;margin:0 0 16px}}
  .stage-card,.side{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}}
  .stage-wrap{{position:relative;width:100%;max-width:420px;margin:0 auto}}
  .stage{{position:relative;width:100%;aspect-ratio:409/1024;overflow:hidden;border-radius:10px;background:#0b1016;box-shadow:inset 0 0 0 1px rgba(255,255,255,.04)}}
  .ghost{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;pointer-events:none;z-index:50}}
  .layer{{position:absolute;inset:0;opacity:0;pointer-events:none;transition:opacity .16s ease;z-index:1}}
  .layer.on{{opacity:1}}
  .layer img{{display:block;width:100%;height:100%;object-fit:fill;user-select:none;-webkit-user-drag:none}}
  .controls{{margin-top:14px}}
  .row{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
  .row label{{font-size:13px;color:var(--muted);min-width:64px}}
  input[type=range]{{flex:1;accent-color:var(--accent);height:28px}}
  .count{{font-variant-numeric:tabular-nums;font-size:13px;min-width:64px;text-align:right}}
  .btns{{display:flex;flex-wrap:wrap;gap:8px}}
  button{{appearance:none;border:1px solid var(--line);background:#243447;color:var(--text);border-radius:8px;padding:8px 12px;font-size:13px;cursor:pointer}}
  button:hover{{border-color:var(--accent)}}
  button.primary{{background:#1f4f73;border-color:#3d89bd}}
  button.active{{background:#2f5a3f;border-color:#5fad7a}}
  .now{{margin-top:8px;padding:10px 12px;border-radius:8px;background:#16202c;border:1px solid var(--line);font-size:13px;line-height:1.45}}
  .now b{{color:var(--accent)}}
  .list{{list-style:none;margin:0;padding:0;display:grid;gap:6px}}
  .list li{{display:grid;grid-template-columns:28px 1fr auto;gap:8px;align-items:center;padding:8px 10px;border-radius:8px;border:1px solid transparent;background:#16202c;font-size:13px;cursor:pointer}}
  .list li.on{{border-color:#3a6b4f;background:#173026}}
  .list li.current{{border-color:var(--accent);box-shadow:0 0 0 1px rgba(91,188,255,.25) inset}}
  .idx{{width:28px;height:28px;border-radius:999px;display:grid;place-items:center;background:#243447;color:var(--muted);font-size:12px}}
  .list li.on .idx{{background:#2f6b4a;color:#dff7ea}}
  .tag{{color:var(--muted);font-size:12px}}
  .ref{{margin-top:14px;border-radius:10px;overflow:hidden;border:1px solid var(--line)}}
  .ref img{{width:100%;display:block}}
  .ref caption{{display:block;padding:8px 10px;font-size:12px;color:var(--muted);background:#16202c}}
  .links a{{color:var(--accent);font-size:12px;margin-right:12px}}
  .metrics{{font-size:12px;color:var(--muted);margin-top:8px}}
</style>
</head>
<body>
  <div class="wrap">
    <section class="stage-card">
      <h1>农场原画 · 图层拆解叠加</h1>
      <p class="sub">Game Art Layer Decomposer：全画布透明层 · 可见区原像素优先 · 进度条逐层叠回。</p>
      <p class="links">
        <a href="Reconstructed/Final.png" target="_blank">打开合成图</a>
        <a href="Validation/Overlay.png" target="_blank">打开对照板</a>
        <a href="Validation/Difference.png" target="_blank">打开差异热力</a>
      </p>
      <div class="stage-wrap">
        <div class="stage" id="stage">
          <img class="ghost" id="ghost" src="Original/Original.png" alt="原图对照">
        </div>
      </div>
      <div class="controls">
        <div class="row">
          <label for="prog">进度</label>
          <input id="prog" type="range" min="0" max="11" step="1" value="0">
          <span class="count" id="count">0 / 11</span>
        </div>
        <div class="row">
          <label for="ghostAmt">原图对照</label>
          <input id="ghostAmt" type="range" min="0" max="70" step="1" value="35">
          <span class="count" id="ghostVal">35%</span>
        </div>
        <div class="btns">
          <button type="button" id="prev">上一层</button>
          <button type="button" id="next" class="primary">下一层</button>
          <button type="button" id="play">自动播放</button>
          <button type="button" id="reset">清空</button>
          <button type="button" id="all">全部叠上</button>
          <button type="button" id="ghostBtn" class="active">原图对照 35%</button>
        </div>
        <div class="now" id="now">当前：<b>空画布</b></div>
        <div class="metrics">重建指标 MAE={report.get('mae')} · PSNR={report.get('psnr')} · SSIM≈{report.get('ssim_luma')}（贴原门；单层另需目视）</div>
      </div>
    </section>
    <aside class="side">
      <h1 style="font-size:16px;margin-bottom:10px">层级（底→顶）</h1>
      <ul class="list" id="list"></ul>
      <figure class="ref">
        <img src="Original/Original.png" alt="原图">
        <caption>对照：原图</caption>
      </figure>
    </aside>
  </div>
<script>
const LAYERS = {json.dumps(layers_js, ensure_ascii=False)};
const stage=document.getElementById("stage");
const list=document.getElementById("list");
const prog=document.getElementById("prog");
const countEl=document.getElementById("count");
const nowEl=document.getElementById("now");
const ghost=document.getElementById("ghost");
const ghostAmt=document.getElementById("ghostAmt");
const ghostVal=document.getElementById("ghostVal");
prog.max=String(LAYERS.length);
LAYERS.forEach((L,i)=>{{
  const div=document.createElement("div");
  div.className="layer";
  div.dataset.i=String(i);
  div.style.zIndex=String(i+1);
  const img=document.createElement("img");
  img.src=L.file; img.alt=L.name;
  div.appendChild(img);
  stage.insertBefore(div,ghost);
  const li=document.createElement("li");
  li.dataset.i=String(i);
  li.innerHTML=`<span class="idx">${{i+1}}</span><span>${{L.name}}<div class="tag">${{L.note||""}}</div></span><span class="tag">z${{i+1}}</span>`;
  list.appendChild(li);
}});
let level=0,timer=null;
function setLevel(n){{
  level=Math.max(0,Math.min(LAYERS.length,n|0));
  prog.value=String(level);
  countEl.textContent=`${{level}} / ${{LAYERS.length}}`;
  stage.querySelectorAll(".layer").forEach(el=>el.classList.toggle("on",Number(el.dataset.i)<level));
  list.querySelectorAll("li").forEach(el=>{{
    const i=Number(el.dataset.i);
    el.classList.toggle("on",i<level);
    el.classList.toggle("current",level>0&&i===level-1);
  }});
  nowEl.innerHTML=level===0?`当前：<b>空画布</b>`:`刚叠上：<b>${{LAYERS[level-1].name}}</b>`;
}}
function setGhost(v){{
  const n=Math.max(0,Math.min(70,Number(v)||0));
  ghostAmt.value=String(n);
  ghost.style.opacity=String(n/100);
  ghostVal.textContent=n?`${{n}}%`:"关";
  const btn=document.getElementById("ghostBtn");
  btn.classList.toggle("active",n>0);
  btn.textContent=n?`原图对照 ${{n}}%`:"开原图对照 35%";
}}
function stopPlay(){{if(timer){{clearInterval(timer);timer=null;}}document.getElementById("play").textContent="自动播放";}}
prog.addEventListener("input",()=>{{stopPlay();setLevel(Number(prog.value));}});
ghostAmt.addEventListener("input",()=>setGhost(ghostAmt.value));
document.getElementById("prev").onclick=()=>{{stopPlay();setLevel(level-1);}};
document.getElementById("next").onclick=()=>{{stopPlay();setLevel(level+1);}};
document.getElementById("reset").onclick=()=>{{stopPlay();setLevel(0);}};
document.getElementById("all").onclick=()=>{{stopPlay();setLevel(LAYERS.length);}};
document.getElementById("ghostBtn").onclick=()=>setGhost(Number(ghostAmt.value)>0?0:35);
document.getElementById("play").onclick=()=>{{
  if(timer){{stopPlay();return;}}
  if(level>=LAYERS.length)setLevel(0);
  document.getElementById("play").textContent="停止";
  timer=setInterval(()=>{{if(level>=LAYERS.length){{stopPlay();return;}}setLevel(level+1);}},700);
}};
list.addEventListener("click",e=>{{
  const li=e.target.closest("li"); if(!li)return;
  stopPlay(); setLevel(Number(li.dataset.i)+1);
}});
setLevel(0); setGhost(35);
</script>
</body>
</html>
"""
    (ROOT / "stack.html").write_text(html, encoding="utf-8")
    print("wrote", ROOT / "stack.html")


def build_prompt(layer: dict) -> str:
    if layer["id"] == "background":
        return (
            "You are a game art cleanup expert. From this winter farm scene, REMOVE all foreground objects "
            "(farmer, sheep, truck, barn, shed, fence, hay bales, trough, tires, props) and fill the holes "
            "with continuous snowy ground, muddy path, distant snow pines and soft blue sky. "
            "Keep original style, lighting, colors. Do not add new decorations. Output a complete clean background plate."
        )
    return (
        "You are a professional game art asset extractor. Extract ONLY this target from the reference crop:\n"
        f"Target: {layer['name']} — {layer.get('prompt_focus','')}\n"
        "Requirements:\n"
        "1. Keep original art style, colors, materials, lighting, perspective.\n"
        "2. Keep original silhouette and proportions; do not redesign.\n"
        "3. Complete only parts hidden by occlusion if needed; do not invent new props.\n"
        "4. True transparent background (real alpha), no white/black/checker matte.\n"
        "5. Preserve anti-aliased edges. This is extraction, not redesign."
    )


def write_prompt_sheet(m):
    lines = []
    for layer in m["layers"]:
        lines.append(f"## {layer['id']}\n")
        lines.append(build_prompt(layer))
        lines.append(f"\nINPUT: _work/crops/{layer['id']}.png")
        lines.append(f"OUTPUT: _work/ai/{layer['id']}.png\n")
    (WORK / "PROMPTS.md").write_text("\n".join(lines), encoding="utf-8")


def main_export():
    m = load_manifest()
    meta = export_crops(m)
    write_prompt_sheet(m)
    print("exported crops + prompts")


def main_recover():
    m = load_manifest()
    meta = json.loads((WORK / "crops_meta.json").read_text(encoding="utf-8"))
    LAYERS.mkdir(parents=True, exist_ok=True)
    # recover object layers first (need masks for bg)
    for layer in sorted(m["layers"], key=lambda x: x["z_index"]):
        if layer["id"] == "background":
            continue
        print("recover", layer["id"])
        canvas = recover_layer(layer["id"], meta, layer.get("needs_inpainting", False))
        out = ROOT / layer["file"]
        canvas.save(out)
        # alpha check
        a = np.array(canvas.getchannel("A"))
        layer["status"] = "done"
        layer["alpha_ok"] = bool((a < 250).mean() > 0.01 and (a > 10).sum() > 100)
        print("  alpha_ok", layer["alpha_ok"], "opaque", int((a > 10).sum()))
    print("recover background")
    bg = recover_background(meta, m)
    # if AI background exists as full scene, also try alpha from difference — keep opaque bg
    bg_path = ROOT / "Layers" / "001_Background.png"
    bg.save(bg_path)
    for layer in m["layers"]:
        if layer["id"] == "background":
            layer["status"] = "done"
            layer["alpha_ok"] = True
    save_manifest(m)
    final = compose(m)
    report = validate(final)
    emit_html(m, report)


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "export"
    if cmd == "export":
        main_export()
    elif cmd == "recover":
        main_recover()
    else:
        raise SystemExit("usage: export|recover")
