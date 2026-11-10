# -*- coding: utf-8 -*-
"""Rebuild preview.html with inlined SVG so file:// keeps currentColor."""
from pathlib import Path

ROOT = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\skill_20261110\icon_b")
ICONS = [
    ("home", "家园"),
    ("bag", "背包"),
    ("map", "地图"),
    ("shop", "商店"),
    ("quest", "任务"),
    ("settings", "设置"),
    ("sprout", "种植"),
    ("watering-can", "浇水"),
]


def js_item(name: str, label: str, svg: str) -> str:
    svg = svg.strip().replace("\\", "\\\\").replace("`", "\\`")
    return f'["{name}", "{label}", `{svg}`]'


items = ",\n".join(
    "      " + js_item(name, label, (ROOT / f"{name}.svg").read_text(encoding="utf-8"))
    for name, label in ICONS
)
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <title>icon.b · 妖精花园线性图标</title>
  <style>
    body {{ margin: 0; font-family: "Segoe UI", "PingFang SC", sans-serif; background: #f3efe4; color: #243028; }}
    header {{ padding: 28px 32px 8px; }}
    h1 {{ font-size: 20px; font-weight: 650; margin: 0 0 6px; }}
    p {{ margin: 0; font-size: 13px; line-height: 1.5; color: #5c6b60; }}
    .grid {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; padding: 20px 32px 36px; }}
    .card {{ background: #fffdf8; border: 1px solid #e4dcc8; border-radius: 16px; padding: 16px 12px 14px; text-align: center; }}
    .sizes {{ display: flex; gap: 14px; justify-content: center; align-items: flex-end; min-height: 52px; color: #2f6a45; }}
    .sizes span {{ display: inline-flex; }}
    .sizes svg {{ width: 100%; height: 100%; }}
    .label {{ margin-top: 10px; font-size: 14px; }}
    .meta {{ margin-top: 2px; font-size: 12px; color: #7d8b80; }}
    .dark {{ margin: 0 32px 32px; padding: 18px 18px 8px; border-radius: 18px; background: #1d3328; color: #e7f2df; }}
    .dark p {{ color: #b7c9b4; padding: 0 8px 12px; }}
    .dark .grid {{ padding: 0 0 18px; }}
    .dark .card {{ background: #274233; border-color: #345544; }}
    .dark .sizes {{ color: #d7e7a8; }}
    .dark .meta {{ color: #9eb5a4; }}
  </style>
</head>
<body>
  <header>
    <h1>妖精花园 · Mode B 线性图标</h1>
    <p>Soft · 24×24 · stroke 2 · round/round · currentColor。每张从左到右是 24、32、48。合同尺寸是 24。</p>
  </header>
  <div class="grid" id="grid-light"></div>
  <section class="dark">
    <p>苔色底预览</p>
    <div class="grid" id="grid-dark"></div>
  </section>
  <script>
    const icons = [
{items}
    ];
    function fill(id) {{
      const grid = document.getElementById(id);
      for (const [name, label, svg] of icons) {{
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `<div class="sizes">
          <span style="width:24px;height:24px">${{svg}}</span>
          <span style="width:32px;height:32px">${{svg}}</span>
          <span style="width:48px;height:48px">${{svg}}</span>
        </div><div class="label">${{label}}</div><div class="meta">${{name}}.svg</div>`;
        grid.appendChild(card);
      }}
    }}
    fill("grid-light");
    fill("grid-dark");
  </script>
</body>
</html>
"""
(ROOT / "preview.html").write_text(html, encoding="utf-8")
print(ROOT / "preview.html")
