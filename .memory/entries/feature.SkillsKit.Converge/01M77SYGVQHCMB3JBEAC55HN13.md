---
id: 01M77SYGVQHCMB3JBEAC55HN13
module: feature.SkillsKit.Converge
entity: ReasonablenessGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_l0_subject_drift
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 合理性修订拦主体锚点丢失与换轨句
verify: unittest tests.test_final_prompt_gate.TestReasonablenessL0 -q
applies: converge reasonableness review 写 revised 时
source:
  conversation: b184581b-9d2c-4d9d-9f09-b09811f9f431
---
需求来源：提示词方向漂移——revised 借合理性闸换题材/丢掉 draft 主体。
必须保持：_l0_subject_drift 在 draft≥8字时，若丢掉≥2个CJK锚点，或 revised 新增换成/改成画风题材/另起炉灶而 draft 没有，则启发式失败；不替代清单。
适用：reasonableness review / 首轮 generate 过闸前。
入口：skills_kit/reasonableness_gate.py _heuristic_issues。
