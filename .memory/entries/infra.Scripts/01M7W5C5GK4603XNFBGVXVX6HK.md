---
id: 01M7W5C5GK4603XNFBGVXVX6HK
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes:
- 01M7VZ88MZ1CC0VQ4GP9C7N6KS
anchors: []
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 超高脚印与引擎精灵asp不一致：先alpha=1 letterbox对齐脚印，再autofit缩小，可gate全ok且幽灵≈23
verify: viking_camp_10 gate ok=10；_ghost_qa mae≈23.2；split_plan compose.autofit=true；_letterbox_to_fp.py
applies: 执行 /pmem-layer-split 且脚印asp与引擎精灵asp差很大时
aliases:
- letterbox autofit
- 脚印比例垫边
source:
  conversation: 21d3f5fa-29b3-495e-a61b-9c3c729e73fb
---
viking_camp_10（超长竖图）交付结论：
- 仅 contain、autofit=false：幽灵可≈23但 asp_err/fill 常 dirty（精灵裁后asp≈0.65，脚印asp≈0.40）。
- 仅 letterbox 填满脚印、autofit=false：gate易全ok，但主体被撑大，幽灵升到≈33 warn。
- 正确组合：对隔离层按冻结脚印 asp 做 alpha=1 letterbox（trim后垫边），compose.autofit=true 用 NCC 缩小对准原图脚印 → gate 10/10 且幽灵 MAE≈23.2 ok。
排除：为过闸只 letterbox 不 autofit；为过幽灵关掉 letterbox 忍受 asp dirty。
