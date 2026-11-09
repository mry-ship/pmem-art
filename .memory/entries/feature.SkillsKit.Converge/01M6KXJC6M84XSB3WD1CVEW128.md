---
id: 01M6KXJC6M84XSB3WD1CVEW128
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/converge_policy.py
- skills_kit/showcase_gate.py#can_accept_winner
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 安全早停默认 0.15/R2；finish 可结算；防回退到 0.5/R4
verify: python3 -c "from skills_kit.converge_policy import DEFAULT_REGRESSION_DROP,
  DEFAULT_EARLY_STOP_MIN_ROUND; assert DEFAULT_REGRESSION_DROP==0.15 and DEFAULT_EARLY_STOP_MIN_ROUND==2"
applies: 所有 converge 会话默认早停
aliases:
- early_safe_stop
- STOP_REGRESSION
- '0.15'
---
现象：评测发现 converge_policy 默认又回到 regression_drop=0.5、early_stop_min_round=4，与 RUN_BRIEF/会话写入的 0.15/R2 分叉。
结论：仓库默认必须保持 0.15 与 R2；
早停后 finish 可挑最高分。
禁止无说明把默认改回 0.5/R4。
