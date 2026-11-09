---
id: 01M6RDTYJNXPTEW2KYWWD9FKGQ
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: correction
status: active
supersedes:
- 01M6R7S9FXP8TH1C2P339D4BHQ
anchors:
- skills_kit/converge.py#_split_speed_requested
- skills_kit/validate_params.py#_round_counts_as_passed
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 多图一轮硬顶认 draw.multi；解剖缺维或导入失败不能停
verify: py -3 -u -m unittest tests.test_skill_speed_caps tests.test_param_validation.TestGateFixes.test_soft_defects_cannot_stop_target
  -q
applies: converge 对多图分工套轮次上限，以及 finish 判一轮是否可停时
aliases:
- draw.multi
- 一轮硬顶
- 缺维
source:
  conversation: 2fb9d6ff-529d-4817-aa0f-d09fd39d062b
---
多图一轮硬顶同时认 route_ids 里的 draw.multi 和 draw.split，以及 expect_route 是这两个。
goal 和 contract 都空、只有 draw.multi 时，_split_speed_requested 为 True，_apply_skill_speed_caps 把 max_rounds 压到 1。
人物/动物/机械/generic 缺少 perspective_anatomy 时，_round_counts_as_passed 为 False。
解剖检查导入或解析抛错也返回 False，不再跳过。
没写 subject_kind 的旧记录仍按原来的缺陷词与已写维度判断。
这两处和路由闸、工作台路径校验已同步到 .claude/worktrees/quizzical-hugle-e0a15e。
