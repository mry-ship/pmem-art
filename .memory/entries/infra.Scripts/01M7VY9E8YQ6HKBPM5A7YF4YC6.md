---
id: 01M7VY9E8YQ6HKBPM5A7YF4YC6
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/compose.py#cover_resize
- scripts/pmem_layer_split/gate.py#_edge_clip_ratio
- scripts/pmem_layer_split/defaults.py
- .cursor/skills/pmem-layer-split/SKILL.md
- assets/viking_camp_10/_ghost_qa.json
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: viking反向：禁非等比压扁；残缺crop会逼换样；须包全+edge_clip
verify: compose 日志 cover_uniform；GATE.edge_clip_max；SKILL §1.3/§4.1；ISOLATE_PROMPT
  含 WHOLE-SUBJECT
applies: 执行 /pmem-layer-split 定块、isolate、compose、gate 时
aliases:
- 背景压扁
- 部位完整
- 切肢
- edge_clip
- 换样
- cover_uniform
source:
  conversation: b7b56b1c-a3f6-44a5-8249-75cbf838c588
---
对 viking_camp_10 成图反向，两处合同缺口已补：

A) 背景压扁
- 原图超长竖比与引擎三档 size 不一致；compose 曾 im.resize((W,H)) 非等比拉伸。
- 现：aspect_pad_rule 出图垫边 + cover_uniform 叠回。

B) 部位完整性
- 枪架/盾 crop 切肢 → 模型另造「完整但换样」精灵，幽灵热点 spear_rack/shield/cabin。
- 木屋框串入角色头 → 另造整屋。
- 现：定块必须包全外轮廓（尖/焰/挂饰/末梢）；
  切肢先扩边；
  咬边难拆优先合槽；
  isolate 提示 WHOLE-SUBJECT COMPLETENESS；
  gate edge_clip≤0.018；
  §4.1 出图后反向验收（贴边/串戏/换样/缺件）再 compose。

排除：残缺 crop 出图指望脑补；为过闸非等比拉伸背景。
