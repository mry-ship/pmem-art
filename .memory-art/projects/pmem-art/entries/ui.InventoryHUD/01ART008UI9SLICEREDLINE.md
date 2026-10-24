---
id: 01ART008UI9SLICEREDLINE
module: ui.InventoryHUD
entity: NineSliceRule
kind: style_redline
status: active
note_date: '2026-10-22'
verified: '2026-10-24'
author: UI主美·温言
summary: 九宫格(9-Slice)弹窗底板严禁在中央拉伸区画圆盘暗纹或斜向花边！四角固定区锁定 48px，外圈必留 4px 透明安全边
verify: 在图谱工作台打开『九宫格切线预览』：48px 切线以内的中央十字区域必须为均匀底色或可平铺肌理，外边缘 4px alpha=0
applies: 所有需要自适应宽高的 UI 弹窗底板、按钮、Tooltip 背景框
aliases: [九宫格红线, 9-slice拉伸变形, UI切图规范]
palette: ["#0F172A", "#1E3A4B", "#F59E0B", "#2DD4BF"]
specs:
  resolution: "512x512"
  nine_slice: [48, 48, 48, 48]
  safe_margin_px: 4
assets:
  - path: assets/ui/modal_frame_9slice_v2.png
    role: approved
    caption: "✅ 正例定稿：四角黄铜雕花严格收在 48x48px 固定区内，中央纯色可任意宽高拉伸，外留 4px 透明边"
    sha256_16: 7196b30bc29ec64a
  - path: assets/ui/modal_frame_rejected_center_ornament.png
    role: rejected
    caption: "❌ 废案打回：AI 在正中央画了大圆盘与对角斜线，Unity 九宫格横向拉宽 3 倍后圆盘被拉成畸形椭圆"
    sha256_16: 8c6504b9d2ff5231
anchors:
  - assets/ui/modal_frame_9slice_v2.png#9slice
  - workflows/comfyui_ui_icon_9slice.json
---
**【UI 九宫格切图防翻车红线】**
AI 美术在生成 UI 边框时，默认喜欢在画布正中心画对称图腾或斜穿全图的金属光泽。
1. **九宫格切线（`[top:48, right:48, bottom:48, left:48]`）**：所有黄铜包角、铆钉、青瓷镶珠**必须 100% 限制在四角 `48x48px` 区域内**。
2. **中央拉伸区（`x: 48~464, y: 48~464`）**：只能是均匀玄青半透明底色（`#0F172A` 95% alpha），严禁出现跨过 48px 切线的斜纹、渐变光斑或中心圆环。
3. **外圈 4px 透明防裁切边距**：画布最外圈 `4px` 必须保持纯透明（`alpha = 0`），防止 Unity Sprite Atlas 打包采样时出现邻图边缘溢色（Texture Bleeding）。
