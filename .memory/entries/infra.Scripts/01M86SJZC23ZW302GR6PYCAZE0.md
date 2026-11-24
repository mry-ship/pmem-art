---
id: 01M86SJZC23ZW302GR6PYCAZE0
module: infra.Scripts
entity: LayerSplitPipeline
kind: correction
status: active
supersedes:
- 01M7T4P333EHEP8XGM8ST08M5Q
anchors:
- skills_kit/agent_router.py#plan_route
- scripts/pmem_layer_split/cli.py
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 拆图层路由已接通；管线仍须把 tighten 开关传进 setup
verify: plan_route('按这张图拆图层并叠回').route_ids==['layer.split']；cli.py pipeline/run-local
  含 tighten_from_bg=_tighten
applies: 维护拆图层技能或 scripts/pmem_layer_split 管线时
source:
  conversation: 8434809b-e30b-410f-9267-50d21ac61575
---
旧结论里「AGENTS.md/CLAUDE.md 与 route 未挂 /pmem-layer-split」已不成立：技能表早已有该技能；
2026-11-24 起 plan_route 对拆图层口语和点名返回 layer.split。
不推翻：pipeline / run-local 必须把 --no-tighten-from-bg 传入 setup_and_calibrate（函数默认仍 tighten=True，不传则关开关无效）。
闸门数字仍与 scripts/pmem_layer_split/defaults.py 同步。
