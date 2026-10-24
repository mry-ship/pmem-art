---
id: 01ART009VFXRECORD
module: vfx.ArcaneSlash
entity: SpriteSheetGrid
kind: asset_record
status: active
note_date: '2026-10-23'
verified: '2026-10-24'
author: 特效师·季燃
summary: 阿斯特拉普攻一阶『星轨秘色刀光』4帧序列帧已入库（1024x512 RGBA，单帧 256x512），已绑定 BattleAstra.prefab
verify: 检查 arcane_slash_4f_sheet.png 尺寸为 1024x512 RGBA，在深灰与浅白底色切换下边缘无黑圈
applies: BattleAstra.prefab 普攻连段第 1~2 击挂点，请勿随意更改单帧宽高比或帧序
palette: ["#F4F1EA", "#F59E0B", "#2DD4BF"]
specs:
  resolution: "1024x512"
  alpha_required: true
  premultiplied_alpha: true
assets:
  - path: assets/vfx/arcane_slash_4f_sheet.png
    role: approved
    caption: "✅ 已入库 4帧横排刀光序列帧（单帧 256x512）：白芯 → 鎏金中层 → 青瓷外焰消散"
    sha256_16: ff106b97f37452f1
anchors:
  - assets/vfx/arcane_slash_4f_sheet.png
---
**【已交付资产台账 · 严禁破坏性覆盖】**
- **资产路径**：`assets/vfx/arcane_slash_4f_sheet.png`（`1024x512`，横排 4 帧，每帧 `256x512`）。
- **色彩层次（由内向外）**：刀刃核心极亮暖白（`#F4F1EA`）→ 中层鎏金（`#F59E0B`）→ 外缘秘色青瓷残影（`#2DD4BF`）。
- **引用保护**：已被客户端 `Assets/Prefabs/VFX/BattleAstra_Slash01.prefab` 按 `UV Tile (4, 1)` 采样并对齐了第 2 帧打击帧判定点，重绘时严禁改变刀光圆心坐标（`cx=128, cy=256`）。
