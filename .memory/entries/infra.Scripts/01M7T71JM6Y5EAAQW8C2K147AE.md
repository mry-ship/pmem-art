---
id: 01M7T71JM6Y5EAAQW8C2K147AE
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes:
- 01M7T3DTXMYWRB9X098VEVHY74
anchors:
- scripts/pmem_layer_split/calibrate.py
- scripts/pmem_layer_split/compose.py#place_scaled
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-19'
summary: Cursor 黑底隔离层叠回前须转近黑为 alpha，并按脚印 letterbox
verify: wine_lounge_6 未转 alpha 时 gate dirty+MAE fail；转 alpha+letterbox 后 gate 6ok
  MAE warn≈44
applies: 执行 /pmem-layer-split 且走 Cursor 黑底回退时
source:
  conversation: bf7d8e5f-c2a9-4e6a-893b-c08ebb46f00e
---
Cursor GenerateImage 无真透明，落盘为不透明纯黑隔离底。
若直接 RGB/全不透明 RGBA 进 compose：trim_alpha 吃满画布 → alpha_mean≈1 判 dirty、fill/asp/feat 全漂、幽灵 MAE 飙升。
正确：近黑→alpha（thr≈28 soft≈10），再按 truth 脚印 letterbox（alpha=1 垫边保 trim 比例），再 compose/gate。
「禁止后抠」指禁止从复杂场景底抠主体；纯隔离黑底板转 alpha 是 Cursor 回退叠回必需步骤。
（合并自叠回锚点结论：踩地底齐、墙挂居中、吊灯顶齐；禁止为过闸撑框。）
