---
id: 01M6M124VHYHR6WNR1HB1AFJAV
module: feature.SkillsKit
entity: ConvergeFinishEarlyStop
kind: feature
status: active
supersedes: []
anchors: []
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: finish 传入 early_safe_stop，安全早停可结算最高分
verified: '2026-11-05'
verified_at: '2026-11-05T20:36:04.523+08:00'
---
需求来源：1105c multi 早停后 finish 被 can_accept_winner 拦住。
必须保持：status=early_safe_stop 或 STOP_PICK_BEST 或 round.early_safe_stop 为 STOP_REGRESSION/PLATEAU 时 finish 传 early_safe_stop=True。
入口：skills_kit/converge.py finish → showcase_gate.can_accept_winner。
