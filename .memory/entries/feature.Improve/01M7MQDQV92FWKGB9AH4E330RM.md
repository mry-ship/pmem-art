---
id: 01M7MQDQV92FWKGB9AH4E330RM
module: feature.Improve
entity: WarmStartGuardrails
kind: correction
status: active
supersedes:
- 01M7MPTT83M2KNMBAXCS9XQNVC
anchors:
- improve/warm_start.py#_task_wants_gh_cabinet_surface
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: FestivalMerge/糖果梯不得吃GH海鲜货柜keep
verify: filter_keeps_for_task(..., prop.FestivalMerge, 糖果合成梯) 无海鲜/龙虾；unittest 含 test_festival_candy_merge_does_not_get_seafood_keeps
applies: Warm-Start 向 *Merge / merge.* 注入 keep 时
source:
  conversation: 7756ad1a-6c4d-4c92-a613-772055b4f6be
---
复查发现 _task_wants_gh_cabinet_surface 曾把 FestivalMerge/糖果/软糖算进货柜任务，导致糖果合成梯仍注入龙虾/海鲜货柜 keep。
更正：仅当 module/goal 命中货柜|Gossip Harbor|海鲜|merge.Harbor* 才注入 GH 表面 keep；糖果/庭院/吉他只留通用五链句。
