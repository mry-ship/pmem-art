---
id: 01M7T4P333EHEP8XGM8ST08M5Q
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/cli.py
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-19'
summary: 二检PASS：技能/defaults/管线对齐；已修pipeline漏传tighten；表未挂
verify: pyw -3 -u assets/wine_lounge_split/_skill_check2.py → RESULT PASS；cli.py pipeline/run-local
  含 tighten_from_bg=_tighten
applies: 维护 /pmem-layer-split 技能与 CLI 时
aliases:
- 技能体检
- layer-split注册
source:
  conversation: 11091f6c-97d6-42cb-87f7-e01a76473eac
---
第二次技能体检 RESULT PASS。
已对齐：三份 SKILL、三份 commands、defaults LOCK LOOK、闸门数字、autofit/footprints/feat_match/scale_mul。
本轮补漏：pipeline 与 run-local 原先未把 --no-tighten-from-bg 传入 setup_and_calibrate（函数默认仍 tighten=True，但关开关无效）——已修。
§3 背景提示已与 BG_ISOLATE_PROMPT 口径对齐。
已知缺口不变：AGENTS.md/CLAUDE.md 技能表与 route 未挂 /pmem-layer-split，点名仍可用。
