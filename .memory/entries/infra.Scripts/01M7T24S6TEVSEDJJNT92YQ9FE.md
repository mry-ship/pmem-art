---
id: 01M7T24S6TEVSEDJJNT92YQ9FE
module: infra.Scripts
entity: LayerSplitPipeline
kind: feature
status: active
supersedes:
- 01M7SZ9NF037J0KKWZYQ4H1H2Y
anchors:
- .cursor/skills/pmem-layer-split/SKILL.md
- scripts/pmem_layer_split/compose.py#autofit_scale_to_ref
- scripts/pmem_layer_split/defaults.py
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-19'
summary: 出图钉死样子视角风格；大小位置可漂，拼回时autofit对准脚印
verify: SKILL 还原合同含「出图钉样子、拼回对准大小位置」；compose 日志有 scale_mul
applies: 执行 /pmem-layer-split 隔离出图与叠回对准时
aliases:
- 样子一模一样
- 拼回对准
- 大小位置可漂
source:
  conversation: 11091f6c-97d6-42cb-87f7-e01a76473eac
---
需求来源：玩家明确口径——出图不只锁风格，还要视角和样子尽量一模一样；大小位置出图时可变化可接受；做好图后由 Agent/管线很快对准位置与大小。
必须保持：
1) isolate 硬锁：同机位/视角、同姿势外形特征、同画风（只拆不换样）；禁止换角、换风、换长相。
2) isolate 时绝对尺度不必死磕；允许略漂。
3) setup 仍写 truth_boxes/_footprints 作槽位真值；compose 用 contain+锚点+autofit_scale_to_ref（及必要微调）快速把大小位置对准脚印；禁止为过闸拧框。
4) 点名 N 部位、gpt-image 优先、Cursor 黑底回退、不展示密钥等既有行为保持。
入口：skills/pmem-layer-split/SKILL.md 还原合同；defaults.ISOLATE_PROMPT；compose.autofit_scale_to_ref。
