---
id: 01M7VY9RTDDM5EM2CF3PN6V798
module: infra.Scripts
entity: LayerSplitPipeline
kind: feature
status: active
supersedes:
- 01M7T24S6TEVSEDJJNT92YQ9FE
anchors:
- scripts/pmem_layer_split/gate.py#_edge_clip_ratio
- scripts/pmem_layer_split/compose.py#cover_resize
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 背景等比cover；脚印锁；部位完整edge_clip；交叠回整图
verify: SKILL §1.3 与 §4.1；GATE.edge_clip_max；compose cover_uniform 日志
applies: 执行 /pmem-layer-split 隔离出图与叠回对准时
aliases:
- 部位完整
- edge_clip
- cover_uniform
source:
  conversation: b7b56b1c-a3f6-44a5-8249-75cbf838c588
---
需求来源：玩家反馈 viking——背景压扁；框定应锁死对象；拼回摆好；并强调单独部位完整性，要求结合成图反向完善技能。
必须保持：
1) isolate 硬锁样子（机位/姿势/特征/画风）以 _crops 为准；keep 短标签。
2) 部位完整性：crop 包全外轮廓；isolate 不贴边裁切；gate edge_clip≤0.018；出图后§4.1反向验收。
3) 背景 aspect_pad_rule + compose cover_uniform，禁止非等比拉伸。
4) 大小可漂、位置靠 footprints+autofit；交 _compose_mid.png + preview + stack.html。
5) 枪架+盾等咬边切肢优先合槽。
入口：pmem-layer-split SKILL 还原合同/§1.3/§3–§5；defaults；gate._edge_clip_ratio；compose.cover_resize。
