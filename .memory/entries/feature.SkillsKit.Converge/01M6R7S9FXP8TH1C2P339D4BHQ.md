---
id: 01M6R7S9FXP8TH1C2P339D4BHQ
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: risk
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_split_speed_requested
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 多图一轮硬顶认 draw.split 但路由是 draw.multi
verify: route_ids=['draw.multi'] 且 goal/contract 为空时 _split_speed_requested 应为 True
applies: converge 对多图分工套 image_round_cap 时
---
_split_speed_requested 用 route_ids 里的 draw.split 判断出图一轮。
注册表与 plan_route 实际写入的是 draw.multi。
只靠 route_ids、goal 里又没有「多图分工/打开这一态」、也没 --contract split 时，硬顶套不上，多图会按普通图最多 4 轮走。
关键词和 contract=split 仍能触发。
