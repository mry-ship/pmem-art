---
id: 01M6NVADB24T5ESRTBG1V7ZEMS
module: feature.SkillsKit
entity: ConvergeFinishEarlyStop
kind: correction
status: active
supersedes:
- 01M6M124VHYHR6WNR1HB1AFJAV
anchors:
- skills_kit/showcase_gate.py#can_accept_winner
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: early_safe 允许 rounds≥1（出图一轮）
verify: can_accept_winner(1, 7.66, early_safe_stop=True) is True
applies: 出图一轮交件 / 安全早停结算
---
旧结论：early_safe_stop 须 rounds≥2 才可低于 9.5 入展陈。
更正：出图一轮硬顶后只有 1 轮，须 rounds≥1 即可；并由 finish 写入「出图一轮交件」供过程板页级识别。STOP_REGRESSION/PLATEAU 的「安全早停」路径不变。
