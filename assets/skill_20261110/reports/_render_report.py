# -*- coding: utf-8 -*-
"""Render the skill-run tables. Paths are relative to reports/."""
import json
from pathlib import Path

root = Path(r"c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\skill_20261110\reports")
rows = json.loads((root / "_digest.json").read_text(encoding="utf-8"))

ORDER = [
    ("draw.ordinary", None, "生图", "普通图"),
    ("draw.key", None, "生图", "原画"),
    ("draw.clone", None, "生图", "克隆"),
    ("draw.variant", None, "生图", "变体"),
    ("draw.multi", None, "生图", "多图分工"),
    ("draw.lens", None, "生图", "镜头包"),
    ("icon.a", None, "图标", "A 桌面母版"),
    ("icon.b", None, "图标", "B 线性 SVG"),
    ("icon.c", None, "图标", "C 道具格"),
    ("ui.kit", None, "界面", "全套"),
    ("merge.ladder", "shop_ladder", "合成梯", "甜品店形变"),
    ("merge.ladder", "same_object", "合成梯", "喷壶同模加装"),
    ("merge.ladder", "species_change", "合成梯", "花园乐器"),
    ("prompt.write", None, "提示词", "三套说法"),
    ("style.lock", None, "锁风格", "样张卡片"),
]


def rel(path: str) -> str:
    if not path:
        return ""
    text = str(path).replace("\\", "/")
    marker = "assets/skill_20261110/"
    if marker in text:
        text = text.split(marker, 1)[1]
    return "../" + text


def find(route_id, variant):
    for row in rows:
        if row["route_id"] == route_id and (row.get("variant") or None) == variant:
            return row
    return None


def fmt_score(value):
    if value is None:
        return "—"
    return f"{float(value):.2f}"


def line_status(row):
    if row["route_id"] in {"draw.lens", "prompt.write", "style.lock"}:
        return "不生图"
    if row["route_id"] == "icon.b":
        return "清单过 · 8.50"
    if row["route_id"] == "icon.c":
        return "批量预览 9.00"
    if row["passed"]:
        return "过线"
    return "未过 9.5"


cards = []
gen_total = 0
for route_id, variant, skill, name in ORDER:
    row = find(route_id, variant)
    thumbs = []
    for image in row["images"]:
        sec = image.get("sec")
        if isinstance(sec, (int, float)):
            gen_total += sec
        label = ""
        if image.get("part"):
            label += str(image["part"]) + " "
        label += f"R{image.get('round')} {fmt_score(image.get('score'))}"
        if sec is not None:
            label += f" · {sec}s"
        src = rel(image.get("path") or "")
        thumbs.append(
            f'<figure><img src="{src}" alt="{name} {label}"><figcaption>{label}</figcaption></figure>'
        )
    final = rel(row.get("final") or "")
    extra = rel(row.get("sheet") or "")
    final_html = "—"
    if final.endswith((".png", ".jpg", ".jpeg", ".webp")):
        final_html = f'<a href="{final}"><img class="hero" src="{final}" alt="{name} 终稿"></a>'
    elif final:
        final_html = f'<a href="{final}">{Path(final).name}</a>'
    if extra:
        final_html += f'<a href="{extra}"><img class="hero" src="{extra}" alt="{name} 组件表"></a>'
    wall = "—"
    if row.get("wall_start") and row.get("wall_end"):
        wall = f'{row["wall_start"][11:16]}–{row["wall_end"][11:16]}'
        if row.get("wall_sec"):
            wall += f'<br>{row["wall_sec"]}s'
    cards.append(
        "<tr>"
        f"<td>{skill}</td><td>{name}</td><td>{line_status(row)}</td>"
        f"<td>{fmt_score(row.get('best'))}</td>"
        f"<td class='shots'>{''.join(thumbs) or '—'}</td>"
        f"<td class='hero-cell'>{final_html}</td>"
        f"<td>{wall}</td>"
        "</tr>"
    )

html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>技能展陈 2026-11-10</title>
<style>
body {{ font-family: "Segoe UI", "Microsoft YaHei", sans-serif; margin: 24px; color: #1c1c1c; background: #f6f4ef; }}
h1 {{ font-size: 22px; margin-bottom: 4px; }}
p.lead {{ max-width: 980px; line-height: 1.55; }}
table {{ border-collapse: collapse; width: 100%; background: #fff; margin: 12px 0 28px; }}
th, td {{ border: 1px solid #ddd; padding: 8px; vertical-align: top; font-size: 13px; }}
th {{ background: #efe8d8; text-align: left; }}
img {{ max-width: 140px; max-height: 100px; display: block; background: #111; }}
img.hero {{ max-width: 220px; max-height: 140px; }}
figure {{ margin: 0 6px 6px 0; display: inline-block; }}
figcaption {{ font-size: 11px; color: #444; }}
.shots {{ min-width: 320px; }}
</style>
</head>
<body>
<h1>技能展陈 2026-11-10 · 妖精花园</h1>
<p class="lead">15 支都已交回。出图闭环没有一支达到 9.5。生图调用合计约 {gen_total} 秒，墙钟从 14:35 到 15:02，各支并行。图标 B、图标 C 用的是清单分，不是 9.5 停机线。镜头包、提示词、锁风格按合同没有出图。</p>

<h2>一、技能与变体</h2>
<table>
<thead><tr><th>技能</th><th>变体</th><th>结果</th><th>最高分</th><th>各轮（分数 · 生图秒）</th><th>终稿</th><th>墙钟</th></tr></thead>
<tbody>
{''.join(cards)}
</tbody>
</table>

<h2>二、反向分析</h2>
<table>
<thead><tr><th>看到的结果</th><th>说明</th><th>下次动哪一层</th></tr></thead>
<tbody>
<tr><td>出图闭环 0 支过 9.5</td><td>最高落在 9.03–9.40：普通图 9.03、图标 A 9.03、乐器 9.09、概念 9.32、组件表 9.40。近优被停机线全部挡住。</td><td>停机线。近优交件和「必须 9.5」要分开写，否则满 4 轮仍一律未过线。</td></tr>
<tr><td>三条合成梯关系都第 1 稿过关，画面都卡在体量</td><td>甜品终稿退回第 1 轮 8.61，第 3 轮掉到 7.89。喷壶最高 8.94，第 3 轮回退早停。乐器满 4 轮 9.09，邻档仍不够陡。</td><td>出图提示词里的体量曲线。关系机读过了，不能当成像素档差已经过了。</td></tr>
<tr><td>多图分工只有关门态</td><td>关门最高 8.58，脚一直在石径旁的圆石上。合同要求第二态只垫已过线的上一张，满轮最高分进不了开门态。</td><td>多图分工的「通过」定义。满轮交件应允许作为下一态的垫图，或单独标明第二态未跑。</td></tr>
<tr><td>变体眼睛过了，嘴不过</td><td>四轮上眼睑都抬过虹膜，嘴一直是竖椭圆，最高 8.52。原句里的「换成」曾让路由 execute_ok 为假，补上「同一张脸，换个表情」才放行。</td><td>局部验收词要可测量，例如「嘴洞宽约等于鼻翼」。路由句不要用「换成」单独当变体信号。</td></tr>
<tr><td>克隆没抄回树屋，身份漂了</td><td>四轮都没有池塘、小船和巨叶框，最高 8.78。脸从兽吻漂到无翅小人，第 4 轮才有小透翅。手仍是连指。原图 169×276 与 3:4 差 18.4%，会话垫图必须加边。</td><td>克隆要另写身份锚，不能只写「不要沿用参考主体」。画幅差超过闸值时，加边文件和生图垫图不是同一张，报表里要分开。</td></tr>
<tr><td>原画守住了构图回声</td><td>样张没有垫进生图，四轮都不是巨叶框加池塘。最高 8.88，剩手指和信纸横线。</td><td>原画这一支的闸是有效的。继续抬分应只改手和纸面，不要把样张垫回去。</td></tr>
<tr><td>图标 A 第 3 轮断崖</td><td>安全区 7.6 时正式分直接取 7.60，第 4 轮回到 9.03。单张只要 16–21 秒。</td><td>门槛维的取分规则。它会把一轮打成断崖，报表要同时留下六维原分。</td></tr>
<tr><td>图标 B / C 的「过」和 9.5 不是一把尺</td><td>B 用 899 秒交了 8 枚 SVG，一致性 8.5 标成通过。C 一张 30 秒，9.0 标成通过，喷壶仍像圆茶壶。</td><td>总表要写明尺子。批量预览的清单通过不能和闭环过线放在同一列里不加注释。</td></tr>
<tr><td>界面爬到 9.3 后几乎不动</td><td>概念 8.64 → 9.32，最后一轮只加 0.02，接触影仍短。组件表 9.14 → 9.40，按下态高度仍接近正常态。结构问题在前两轮已经修好。</td><td>第 4 轮只改接触影或按下高度。继续整张重画会把已经对的顶栏和主按钮冲掉。</td></tr>
<tr><td>锁风格在并行时没写完口味档案</td><td>三条记忆落在 brand.SkillRun20261110，耗时 446 秒。口味档案因为文件被占用跳过了。</td><td>并行全检不要同时写同一份口味档案。风格卡片本身可以独立验收。</td></tr>
<tr><td>提示词的风格默认离开了本趟文字风格</td><td>62 秒，三套都标普通图，正确地没有生图。没有风格句时落到水彩绘本，和全清单的软塑胶不是同一句。</td><td>全清单要给提示词一支同样的风格句，否则它会按品类默认另起一套。</td></tr>
<tr><td>整表生图比图标慢一个数量级</td><td>图标 A 单张约 20 秒。甜品整表两轮是 202 秒和 220 秒。乐器后两轮只有 17 秒和 21 秒，和前两轮的 79、70 秒差很多，计时口径不完全一样。</td><td>耗时表分开写「生图调用」和「墙钟」。后两轮极短的秒数要核对是不是只记了落盘差。</td></tr>
<tr><td>预览服务和 pyw</td><td>用 pyw 开的 http.server 几秒就退出。改用 python.exe 后，18923 上的 preview.html 返回了 200。</td><td>看 SVG 预览不要用 pyw 起服务。</td></tr>
<tr><td>审图、归档、教练没有单独开跑</td><td>这三支不产生本页的成图。上面的表就是这批结果的审读。现在跑归档会把这些过程图扫进总图谱。</td><td>要进图谱时再点名归档。教练看的是跨次进步，不替代这张结果表。</td></tr>
</tbody>
</table>
</body>
</html>
"""
(root / "index.html").write_text(html, encoding="utf-8")
print(root / "index.html")
print("gen_total", gen_total)
