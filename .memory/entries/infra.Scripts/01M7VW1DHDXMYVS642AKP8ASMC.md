---
id: 01M7VW1DHDXMYVS642AKP8ASMC
module: infra.Scripts
entity: LayerSplitPipeline
kind: decision
status: active
supersedes: []
anchors: []
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 玩家要「不扣」时交原图矩形裁切 crops_raw，不做黑底转 alpha
verify: wine_lounge_10/crops_raw 有 10 张矩形裁切 + crops_raw.html
applies: 玩家点名不抠/直接拆/只要裁切时
---
隔离层走 Cursor 黑底再转 alpha 常扣脏（木色/暗影被当黑底吃掉）。玩家明确说「直接拆出来不扣」时：交付 setup 的 `_crops` 矩形块（或导出到 crops_raw/），不做 AI 隔离、不做近黑→alpha。
代价：框内仍带邻居/背景，不能当透明装修精灵叠回；要透明叠回仍须 gpt-image 真透明或接受隔离扣边风险。
