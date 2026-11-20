---
id: 01M7W3KEHWQ5GFVGNXADR5HSHD
module: infra.Scripts
entity: LayerSplitPipeline
kind: feature
status: active
supersedes:
- 01M7VY9RTDDM5EM2CF3PN6V798
anchors:
- scripts/pmem_layer_split/defaults.py
- scripts/pmem_layer_split/calibrate.py
- scripts/pmem_layer_split/isolate.py
- skills_kit/data/pmem_layer_split_skill_body.md
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: isolate双垫crop+ctx；框pad0.05；禁一次出齐N层
verify: setup 生成 *_ctx.png；isolate 命令含两个 --image；SKILL §4.0
applies: 执行 /pmem-layer-split 隔离出图与定块时
aliases:
- 双垫
- ctx
- 框够大
source:
  conversation: 8bf3f9f2-0d6e-45db-b55e-017394ead677
---
需求来源：玩家要求拆层技能优化到「框够大、隔离跟原图像」；质疑紧 crop 与一次整表出图。
必须保持：
1) 定块 pad≥0.05；setup 写出宽松 crop + <id>_ctx 整图高亮；isolate 双垫。
2) footprints 仍用剪影+垫做叠回槽；isolate crop 可再扩 EXTRA。
3) 逐层出图（非一次 N 透明层）；交 layers.md 可点表。
入口：pmem-layer-split SKILL §1.1/§4.0；defaults；calibrate；isolate。
