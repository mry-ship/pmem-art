# -*- coding: utf-8 -*-
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parent
PLACE = json.loads((ROOT / "_placements_v3.json").read_text(encoding="utf-8"))
OUT = ROOT / "stack_v3.html"

layers_js = ",\n".join(
    "  {{id:'{id}', name:{name}, file:'{file}', left:{left:.4f}, top:{top:.4f}, "
    "width:{width:.4f}, height:{height:.4f}, note:{note}, bg:{bg}}}".format(
        id=p["id"],
        name=json.dumps(p["name"], ensure_ascii=False),
        file=p["file"],
        left=p["left"],
        top=p["top"],
        width=p["width"],
        height=p["height"],
        note=json.dumps(p.get("note", ""), ensure_ascii=False),
        bg="true" if p["id"] == "bg" else "false",
    )
    for p in PLACE
)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>农场77 · 切块锁位叠图 v3</title>
<style>
  :root {{ --bg:#121820; --panel:#1c2633; --line:#314255; --text:#e8eef6; --muted:#93a4b8; --accent:#5bbcff; }}
  *{{box-sizing:border-box}}
  body{{margin:0;min-height:100vh;color:var(--text);background:radial-gradient(1200px 600px at 20% -10%,#243247 0%,var(--bg) 55%);
    font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif}}
  .wrap{{max-width:1240px;margin:0 auto;padding:20px 18px 40px;display:grid;grid-template-columns:minmax(300px,460px) 1fr;gap:22px}}
  @media (max-width:900px){{.wrap{{grid-template-columns:1fr}}}}
  h1{{font-size:20px;margin:0 0 6px;font-weight:650}}
  .sub{{color:var(--muted);font-size:13px;line-height:1.5;margin:0 0 16px}}
  .stage-card,.side{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}}
  .stage-wrap{{position:relative;width:100%;max-width:420px;margin:0 auto}}
  .stage{{position:relative;width:100%;aspect-ratio:409/1024;overflow:hidden;border-radius:10px;background:#0b1016;
    box-shadow:inset 0 0 0 1px rgba(255,255,255,.04)}}
  .stage img{{position:absolute;pointer-events:none;user-select:none}}
  .row{{display:flex;align-items:center;gap:10px;padding:8px 4px;border-bottom:1px solid rgba(255,255,255,.06)}}
  .row label{{flex:1;font-size:13px}}
  .row small{{color:var(--muted);font-size:11px}}
  input[type=range]{{width:100%;margin:10px 0 4px}}
  .prog{{font-size:12px;color:var(--accent)}}
</style>
</head>
<body>
<div class="wrap">
  <div class="stage-card">
    <h1>农场77 · 切块锁位 v3</h1>
    <p class="sub">方法：原图切块 → 提示词隔离补遮挡 → 贴回同一裁切框。允许遮挡重叠；食槽边羊并入食槽块；轮胎羊含旁侧木板细节。</p>
    <div class="stage-wrap"><div class="stage" id="stage"></div></div>
    <input id="slider" type="range" min="0" max="0" value="0">
    <div class="prog" id="prog"></div>
  </div>
  <div class="side">
    <div id="list"></div>
  </div>
</div>
<script>
const LAYERS = [
{layers_js}
];
const stage=document.getElementById("stage");
const list=document.getElementById("list");
const prog=document.getElementById("prog");
const slider=document.getElementById("slider");
const imgs=[];
LAYERS.forEach((L,i)=>{{
  const img=document.createElement("img");
  img.src=L.file;
  img.alt=L.name;
  img.style.left=(L.left*100)+"%";
  img.style.top=(L.top*100)+"%";
  img.style.width=(L.width*100)+"%";
  img.style.height=(L.height*100)+"%";
  img.style.objectFit=L.bg?"cover":"contain";
  img.style.opacity="0";
  stage.appendChild(img);
  imgs.push(img);
  const row=document.createElement("div");
  row.className="row";
  row.innerHTML=`<label><input type="checkbox" data-i="${{i}}" checked> ${{L.name}}</label><small>${{L.note||""}}</small>`;
  list.appendChild(row);
}});
slider.max=String(LAYERS.length);
slider.value=String(LAYERS.length);
function render(){{
  const n=+slider.value;
  imgs.forEach((img,i)=>{{
    const on=list.querySelector(`input[data-i="${{i}}"]`).checked && i<n;
    img.style.opacity=on?"1":"0";
  }});
  prog.textContent=n===0?"（空）":`显示 1–${{n}} / ${{LAYERS.length}}：${{LAYERS.slice(0,n).map(x=>x.name).join(" → ")}}`;
}}
slider.addEventListener("input",render);
list.addEventListener("change",render);
render();
</script>
</body>
</html>
"""
OUT.write_text(html, encoding="utf-8")
print("wrote", OUT)
