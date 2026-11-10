---
id: 01M726NMVTH4N4BEGG1BMABN7X
module: feature.SkillsKit.MergeLadder
entity: MergeStyleDefault
kind: correction
status: active
supersedes:
- 01M70V8STCYQ68P2TBX9WBX8KJ
anchors:
- skills_kit/merge_relation.py#merge_surface_lock_line
- skills_kit/merge_relation.py#audit_overview_sheet
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 合成梯没写风格就钉软塑胶；整表只锁格子
verify: rg "没写风格时，即使有整表参考，也钉 Merge Mansion 软塑胶" skills_kit/skill_specs.py；python -m
  unittest tests.test_delivery_gates.DeliveryGateTests.test_merge_without_style_is_soft_plastic
  tests.test_delivery_gates.DeliveryGateTests.test_overview_volume_rejects_flat_neighbors
  -q
applies: 跑合成梯且玩家没另点画风时。玩家写了写实/水彩等则跟文字
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
现象：甜品整表没写风格，垫了写实感的格子参考，成图跟着参考偏写实。
旧结论「无文字跟参考表面」对合成梯整表不再成立。玩家没写风格时，即使有整表格子，也钉 Merge Mansion 软塑胶；格子只锁版式。只有玩家写出写实、水彩、赛博等才离开软塑胶。
关系稿机读通过不等于整表过线。邻档主体框高几乎一样大，本轮不能过线。
文字风格仍然优先于参考。非 merge 品类仍禁止套软塑胶。
