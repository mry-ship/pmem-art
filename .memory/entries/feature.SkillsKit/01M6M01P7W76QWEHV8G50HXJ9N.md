---
id: 01M6M01P7W76QWEHV8G50HXJ9N
module: feature.SkillsKit
entity: ReasonablenessGate
kind: feature
status: active
supersedes: []
anchors: []
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 合理性闸恢复：UI禁叙事垫/IconA满幅/split状态机/软糖/merge链型+早停入展
verify: python3 -m pytest tests/test_reasonableness_gate.py tests/test_merge_relation.py
  tests/test_showcase_gate.py -q
applies: 跑 converge generate / showcase finish / relation-judge 时
---
需求来源：1105c 调整前闸门部分回退。
必须保持：UI禁叙事垫图+控件工艺+CTA避脸；
IconA满幅直角；
split状态机；
软糖SSS；
merge链型与母体/形变句；
showcase can_accept_winner(early_safe_stop)；
EN↔CJK与换货主语闸。
入口：reasonableness_gate/merge_relation/showcase_gate
