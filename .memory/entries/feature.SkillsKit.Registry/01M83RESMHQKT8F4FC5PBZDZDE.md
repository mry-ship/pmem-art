---
id: 01M83RESMHQKT8F4FC5PBZDZDE
module: feature.SkillsKit.Registry
entity: LayerSplitPack
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/data/pmem_layer_split_skill_body.md
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆层执行卡：吞邻框禁止出图，略小不重抽
verify: 执行卡第6步：对照 crop 没过禁止 compose；谁压谁错了改回定块
applies: 跑 /pmem-layer-split，执行侧只读执行卡加交件可见
aliases:
- 定块
- 执行卡
source:
  kind: human
---
需求来源：展陈拆层定块错了仍出图。执行包只装执行卡。
必须保持：执行卡先定谁压谁；
地面留背景；一框一件；
同一件一个 keep；
guide 吞邻禁止 isolate。
isolate 后先对照 crop，换样才重抽，没过禁止 compose。
叠回之后谁压谁错了改回定块。
略小不重抽。
重抽只写零件，不写 MAE、scale、fill。
适用：每次 /pmem-layer-split。入口：skills_kit/data/pmem_layer_split_skill_body.md 执行卡。
