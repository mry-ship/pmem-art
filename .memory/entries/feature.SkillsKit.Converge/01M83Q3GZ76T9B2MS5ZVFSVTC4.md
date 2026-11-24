---
id: 01M83Q3GZ76T9B2MS5ZVFSVTC4
module: feature.SkillsKit.Converge
entity: ParallelSlotGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/parallel_slots.py#assert_can_start
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: converge start 按 max_parallel 硬拦活跃会话槽
verify: tests.test_hard_pits_gates.TestParallelSlots
applies: converge start
verified: '2026-11-24'
verified_at: '2026-11-24T23:02:55.714+08:00'
source:
  kind: conversation
---
需求来源：全技能展陈超 agent.max_parallel。
必须保持：start 扫描 .memory-art/converge/*.json 非 finished 会话，数量≥max_parallel 则拒绝新开（同 session_id 可重开）。
入口：parallel_slots.assert_can_start。
