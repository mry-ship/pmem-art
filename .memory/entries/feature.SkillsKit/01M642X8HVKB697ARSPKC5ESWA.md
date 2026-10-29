---
id: 01M642X8HVKB697ARSPKC5ESWA
module: feature.SkillsKit
entity: AnatomyVeto
kind: exclusion
status: seed
supersedes: []
anchors:
- skills_kit/converge_policy.py#anatomy_ok_for_stop
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 角色透视解剖低于7.5不能停，缺维fail-closed
verify: anatomy_ok_for_stop 在缺维或<7.5时为 False
applies: 人物/动物/机械生图闭环
aliases:
- 解剖否决
- '7.5'
---
依据 7bfa6b5 与 converge_policy.anatomy_ok_for_stop。
人物、动物、机械的透视解剖低于 7.5 不能停，缺这一维 fail-closed。
纯场景不套 7.5，除非缺陷写了结构塌缩。
像素/Q版/平涂也不把这条线打折。
排除：用氛围分把解剖不合格的角色图停机。
