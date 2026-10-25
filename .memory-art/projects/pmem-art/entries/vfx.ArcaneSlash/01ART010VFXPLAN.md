---
id: 01ART010VFXPLAN
module: vfx.ArcaneSlash
entity: ColorRamp
kind: art_plan
status: active
note_date: '2026-10-24'
author: 特效师·季燃
summary: 待产资产需求单：大招『周天星盘碎裂』受击爆点 8帧序列帧（2048x512 RGBA，引入 15% 朱砂绛红 #E11D48 裂纹）
verify: 待产（磁盘尚无此文件）；现行已交付资产仅为 assets/vfx/arcane_slash_4f_sheet.png。交付 8f 后再跑 pmem_art.py validate
applies: 角色终极技能第 3 段全屏爆发阶段
palette: ["#F4F1EA", "#F59E0B", "#2DD4BF", "#E11D48"]
specs:
  resolution: "2048x512"
  alpha_required: true
anchors: []
---
**【待生成美术需求单（Art Plan · 未交付）】**
- **目标文件（尚未存在）**：`assets/vfx/astrolabe_burst_8f_sheet.png`
- **现行已交付**：`assets/vfx/arcane_slash_4f_sheet.png`（`1024x512` 横排 4 帧）
- **规格参数**：`2048x512`（横排 8 帧，单帧 `256x512`），`RGBA` 预乘透明通道。
- **视觉要求**：前 3 帧为黄铜星盘急速坍缩聚光（`#F59E0B`），第 4 帧迸发出朱砂绛红（`#E11D48`）与秘色青瓷（`#2DD4BF`）交织的几何星轨碎片，第 5~8 帧化作星尘消散。
