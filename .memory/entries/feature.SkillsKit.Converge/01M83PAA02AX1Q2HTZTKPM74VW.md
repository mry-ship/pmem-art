---
id: 01M83PAA02AX1Q2HTZTKPM74VW
module: feature.SkillsKit.Converge
entity: ReasonablenessFalsePositive
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_heuristic_issues
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 合理性闸：插画垫否定分字段；L0改写软保留
verify: tests.test_reasonableness_gate.TestReview.test_ui_ban_illust_pad_phrase_not_false_positive；tests.test_final_prompt_gate.TestReasonablenessL0
applies: converge discuss 合理性闸
source:
  kind: conversation
---
需求来源：展陈 UI/普通图合理性误拦。
必须保持：ui 插画垫禁令只对未被否定的命中报错，draft/revised/notes 分开；
L0 同题材改写不报漂移，真换题材仍报。
入口：review_reasonableness/_heuristic_issues/_l0_subject_drift。
