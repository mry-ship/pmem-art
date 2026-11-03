# -*- coding: utf-8 -*-
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
placed = json.loads((ROOT / "_placements_v2.json").read_text(encoding="utf-8"))

js_layers = []
for p in placed:
    bg = ", bg:true" if p["id"] == "bg" else ""
    js_layers.append(
        "{{id:{id!r}, name:{name!r}, file:{file!r}, left:{left:.4f}, top:{top:.4f}, "
        "width:{width:.4f}, height:{height:.4f}, note:{note!r}{bg}}}".format(
            id=p["id"],
            name=p["name"],
            file=p["file"],
            left=p["left"],
            top=p["top"],
            width=p["width"],
            height=p["height"],
            note=p.get("note") or "",
            bg=bg,
        )
    )
layers_js = ",\n  ".join(js_layers)

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>农场77 · 新图槽位叠加 v2（真值整包）</title>
<style>
  :root {{
    --bg:#121820; --panel:#1c2633; --line:#314255;
    --text:#e8eef6; --muted:#93a4b8; --accent:#5bbcff;
  }}
  *{{box-sizing:border-box}}
  body{{
    margin:0;min-height:100vh;color:var(--text);
    background:radial-gradient(1200px 600px at 20% -10%,#243247 0%,var(--bg) 55%);
    font-family:"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;
  }}
  .wrap{{
    max-width:1240px;margin:0 auto;padding:20px 18px 40px;
    display:grid;grid-template-columns:minmax(300px,460px) 1fr;gap:22px;
  }}
  @media (max-width:900px){{.wrap{{grid-template-columns:1fr}}}}
  h1{{font-size:20px;margin:0 0 6px;font-weight:650}}
  .sub{{color:var(--muted);font-size:13px;line-height:1.5;margin:0 0 16px}}
  .stage-card,.side{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px}}
  .stage-wrap{{position:relative;width:100%;max-width:420px;margin:0 auto}}
  .stage{{
    position:relative;width:100%;aspect-ratio:409/1024;overflow:hidden;
    border-radius:10px;background:#0b1016;
    box-shadow:inset 0 0 0 1px rgba(255,255,255,.04);
  }}
  .ghost{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0;pointer-events:none;z-index:50}}
  .layer{{position:absolute;opacity:0;pointer-events:none;transition:opacity .16s ease;z-index:1}}
  .layer.on{{opacity:1}}
  .layer img{{
    display:block;width:100%;height:100%;object-fit:fill;
    user-select:none;-webkit-user-drag:none;
    filter:drop-shadow(0 6px 10px rgba(0,0,0,.25));
  }}
  .layer.bg img{{object-fit:cover;filter:none}}
  .controls{{margin-top:14px}}
  .row{{display:flex;align-items:center;gap:10px;margin-bottom:10px}}
  .row label{{font-size:13px;color:var(--muted);min-width:64px}}
  input[type=range]{{flex:1;accent-color:var(--accent);height:28px}}
  .count{{font-variant-numeric:tabular-nums;font-size:13px;min-width:64px;text-align:right}}
  .btns{{display:flex;flex-wrap:wrap;gap:8px}}
  button{{
    appearance:none;border:1px solid var(--line);background:#243447;color:var(--text);
    border-radius:8px;padding:8px 12px;font-size:13px;cursor:pointer;
  }}
  button:hover{{border-color:var(--accent)}}
  button.primary{{background:#1f4f73;border-color:#3d89bd}}
  button.active{{background:#2f5a3f;border-color:#5fad7a}}
  .now{{margin-top:8px;padding:10px 12px;border-radius:8px;background:#16202c;border:1px solid var(--line);font-size:13px;line-height:1.45}}
  .now b{{color:var(--accent)}}
  .list{{list-style:none;margin:0;padding:0;display:grid;gap:6px}}
  .list li{{
    display:grid;grid-template-columns:28px 1fr auto;gap:8px;align-items:center;
    padding:8px 10px;border-radius:8px;border:1px solid transparent;background:#16202c;
    font-size:13px;cursor:pointer;
  }}
  .list li.on{{border-color:#3a6b4f;background:#173026}}
  .list li.current{{border-color:var(--accent);box-shadow:0 0 0 1px rgba(91,188,255,.25) inset}}
  .idx{{width:28px;height:28px;border-radius:999px;display:grid;place-items:center;background:#243447;color:var(--muted);font-size:12px}}
  .list li.on .idx{{background:#2f6b4a;color:#dff7ea}}
  .tag{{color:var(--muted);font-size:12px}}
  .ref{{margin-top:14px;border-radius:10px;overflow:hidden;border:1px solid var(--line)}}
  .ref img{{width:100%;display:block}}
  .ref caption{{display:block;padding:8px 10px;font-size:12px;color:var(--muted);background:#16202c}}
  .links a{{color:var(--accent);font-size:12px;margin-right:12px}}
</style>
</head>
<body>
  <div class="wrap">
    <section class="stage-card">
      <h1>新图槽位叠加 v2</h1>
      <p class="sub">整包重做：真值框 → 严格隔离拆件（new_v2）→ 一次叠图。卡车朝左下；谷仓按原图高度锁定并可溢出裁切。默认开原图对照。</p>
      <p class="links">
        <a href="_compose_v2_preview.png" target="_blank">打开对照板</a>
        <a href="_truth_guide.png" target="_blank">打开真值框</a>
      </p>
      <div class="stage-wrap">
        <div class="stage" id="stage">
          <img class="ghost" id="ghost" src="ref_new_full.jpg" alt="原图对照">
        </div>
      </div>
      <div class="controls">
        <div class="row">
          <label for="prog">进度</label>
          <input id="prog" type="range" min="0" max="10" step="1" value="0">
          <span class="count" id="count">0 / 10</span>
        </div>
        <div class="row">
          <label for="ghostAmt">原图对照</label>
          <input id="ghostAmt" type="range" min="0" max="70" step="1" value="40">
          <span class="count" id="ghostVal">40%</span>
        </div>
        <div class="btns">
          <button type="button" id="prev">上一层</button>
          <button type="button" id="next" class="primary">下一层</button>
          <button type="button" id="play">自动播放</button>
          <button type="button" id="reset">清空</button>
          <button type="button" id="all">全部叠上</button>
          <button type="button" id="ghostBtn" class="active">原图对照 40%</button>
        </div>
        <div class="now" id="now">当前：<b>空画布</b></div>
      </div>
    </section>
    <aside class="side">
      <h1 style="font-size:16px;margin-bottom:10px">层级（底→顶 · 真值顺序）</h1>
      <ul class="list" id="list"></ul>
      <figure class="ref">
        <img src="ref_new_full.jpg" alt="原新图">
        <caption>对照：原新图整图</caption>
      </figure>
    </aside>
  </div>
<script>
const LAYERS = [
  {layers_js}
];

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
  div.className="layer"+(L.bg?" bg":"");
  div.dataset.i=String(i);
  div.style.left=(L.left*100)+"%";
  div.style.top=(L.top*100)+"%";
  div.style.width=(L.width*100)+"%";
  div.style.height=(L.height*100)+"%";
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
  nowEl.innerHTML=level===0?`当前：<b>空画布</b>`:`刚叠上：<b>${{LAYERS[level-1].name}}</b> — ${{LAYERS[level-1].note||""}}`;
}}
function setGhost(v){{
  const n=Math.max(0,Math.min(70,Number(v)||0));
  ghostAmt.value=String(n);
  ghost.style.opacity=String(n/100);
  ghostVal.textContent=n?`${{n}}%`:"关";
  const btn=document.getElementById("ghostBtn");
  btn.classList.toggle("active",n>0);
  btn.textContent=n?`原图对照 ${{n}}%`:"开原图对照 40%";
}}
function stopPlay(){{if(timer){{clearInterval(timer);timer=null;}}document.getElementById("play").textContent="自动播放";}}
prog.addEventListener("input",()=>{{stopPlay();setLevel(Number(prog.value));}});
ghostAmt.addEventListener("input",()=>setGhost(ghostAmt.value));
document.getElementById("prev").onclick=()=>{{stopPlay();setLevel(level-1);}};
document.getElementById("next").onclick=()=>{{stopPlay();setLevel(level+1);}};
document.getElementById("reset").onclick=()=>{{stopPlay();setLevel(0);}};
document.getElementById("all").onclick=()=>{{stopPlay();setLevel(LAYERS.length);}};
document.getElementById("ghostBtn").onclick=()=>setGhost(Number(ghostAmt.value)>0?0:40);
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
setLevel(0); setGhost(40);
</script>
</body>
</html>
"""

# fix f-string accidental double braces for JS - we used {{ for literal braces in f-string
# but layers_js insertion used {layers_js} which is correct
out = ROOT / "stack_v2.html"
# The html above has doubled braces for JS template - good for f-string
# But I used {layers_js} - need to substitute
html = html.replace("{layers_js}", layers_js)
out.write_text(html, encoding="utf-8")
print("wrote", out)
