---
id: 01M759W9JP7WYVAGN805HY3SKX
module: feature.SkillsKit.Converge
entity: ReasonablenessGate
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#check_reasonableness_gate
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 首轮 prompt≠revised 拒绝静默替换
verify: unittest tests.test_reasonableness_gate.TestReasonablenessSession.test_first_generate_rejects_unreviewed_prompt
  -q
applies: converge generate 首轮过合理性闸时
aliases:
- 拒绝静默替换
- 首轮 revised
verified: '2026-11-11'
verified_at: '2026-11-11T21:41:56.506+08:00'
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧行为：首轮 generate 若 --prompt 与 revised 不同，仍强制用 revised 并提示「已忽略未再审的 --prompt」。
更正：不一致时闸门失败，要求重跑 reasonableness review 或省略/--prompt 对齐 revised；空 prompt 或等于 draft/revised 仍注入 revised。
目的：禁止静默改词造成「改了没用」的非理性感。
