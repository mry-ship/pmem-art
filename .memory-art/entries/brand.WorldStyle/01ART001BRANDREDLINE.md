---
id: 01ART001BRANDREDLINE
module: brand.WorldStyle
entity: ColorRatio
kind: style_redline
status: active
scope: project
note_date: '2026-10-18'
verified: '2026-10-24'
author: 主美·林岚
summary: 严禁使用高饱和赛博洋红(#FF00FF)/电光青(#00FFFF)，全项目必须死守 70/20/10 玄青-青瓷-鎏金配比
verify: 使用色板检查器采样画面高饱和洋红/荧光紫像素占比必须为 0%，主暗部色相落在 200°~225°(玄青/黛蓝)
applies: 全项目所有角色、场景、UI 与宣传图（除受击警示特效可用 #E11D48 朱砂红外）
aliases: [禁用赛博霓虹, 色彩红线, 70-20-10法则]
palette: ["#0F172A", "#1E3A4B", "#2DD4BF", "#F4F1EA", "#F59E0B"]
assets:
  - path: assets/brand/world_color_script_v2.png
    role: approved
    caption: "✅ 正例基准：70%玄青黛蓝底色 + 20%秘色青瓷与宣纸白 + 10%鎏金点睛"
    sha256_16: fd933f6a747df531
  - path: assets/brand/rejected_neon_cyber_v1.png
    role: rejected
    caption: "❌ 废案警示：AI 默认泛化出的洋红/电光青赛博霓虹色调，彻底破坏东方青瓷古雅氛围"
    sha256_16: 740f531afca04699
anchors:
  - assets/brand/world_color_script_v2.png#palette
---
**【主美红线·全项目强制】**
AI 生图模型在遇到“星盘、机械义眼、浮空遗迹、发光法阵”等关键词时，极易滑向西方赛博朋克的高饱和洋红（`#FF00FF`）、荧光紫（`#9333EA`）与刺眼电光青（`#00FFFF`）。

1. **70% 主基调（环境与大面积服饰暗面）**：必须使用沉稳的玄青夜色（`#0F172A`）与远山黛蓝（`#1E3A4B`）。
2. **20% 辅助调（灵脉与受光亮面）**：使用温润半哑光的秘色青瓷（`#2DD4BF`）与宣纸暖白（`#F4F1EA`）。
3. **10% 点睛色（视觉焦点）**：仅在星盘刻度、衣服镶边、核心符文处使用鎏金（`#F59E0B`）。
4. **全局必加负向词（Negative Prompt）**：`cyberpunk, neon magenta, hot pink, electric cyan, oversaturated purple, synthwave, plastic gloss`。
