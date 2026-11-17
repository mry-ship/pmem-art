---
id: 01M7MPTT83M2KNMBAXCS9XQNVC
module: feature.Improve
entity: WarmStartGuardrails
kind: correction
status: active
supersedes:
- 01M7MP0Y8JGM3REFZBPXBK20B3
anchors:
- improve/warm_start.py#filter_keeps_with_audit
- improve/warm_start.py#_task_wants_gh_cabinet_surface
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: GH货柜keep不得骑非货柜merge；知识卡侧逆光/Q版须点名
verify: unittest tests.test_warm_start_guardrails -q；instrument merge pack 无海鲜；ui
  pack 无厚涂
applies: Warm-Start 注入对非对应用户任务时
source:
  conversation: 7756ad1a-6c4d-4c92-a613-772055b4f6be
---
深度审计后补强：
1) keep：含货柜/糖釉/海鲜/龙虾/#FEFDFB 等表面句，仅当任务像货柜/糖果/GH（goal/module 命中）才注入；吉他等 prop.*Merge 只留通用五链句。
2) 知识卡：UI/图标禁厚涂水彩赛璐珞与侧逆光Q版；light-rim 须目标含侧逆光；style-chibi 须 Q版/头身/吉祥物。
3) _is_merge_module 仍只认 merge.*，避免扩大后误杀 FestivalMerge 的「黑底整表」糖果禁令。
不新增用户确认。
