---
id: 01M642X9DXH0NFC3GC0GDS3ZJ4
module: feature.SkillsKit
entity: PadBestPlate
kind: correction
status: seed
supersedes: []
anchors:
- skills_kit/converge.py
- skills_kit/skill_specs.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 已推翻垫最高分成图，每轮只垫最初参考图
verify: converge generate 垫的是 start 时的参考图而不是最高分轮次图
applies: 有参考图的四档闭环
aliases:
- 垫最高分
- 垫上一轮
---
依据提交 3070e76 曾把后续轮垫在最高分成图上，现行代码已改为每轮垫最初参考图。这是被推翻的方向：垫最高分板会把贴原和未换机位锁死。排除：为了「稳定」把上一轮或最高分成图垫回去。
