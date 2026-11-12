---
id: 01M750C1ZNTX46W3QS85PMCPAP
module: feature.SkillsKit.Converge
entity: PriorReusePadGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/prior_reuse_gate.py#assert_no_silent_prior_asset_reuse
- skills_kit/converge.py#_resolve_pad_auto
- skills_kit/converge.py#_merge_no_ref_forbid_prev_plate
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: start拒静默旧交付路径；merge无参考禁垫上轮
verify: py -3 -m unittest tests.test_prior_reuse_gate -v
applies: converge start；merge.* 无 style_ref 的 generate 垫图策略
aliases:
- 接旧轨闸
- merge无参考
- pad=previous
source:
  conversation: 7f6eb6c5-c94f-491f-9845-6667f9d3d230
---
需求来源：未点名接续却垫/引用 assets/skill_* 旧交付，merge 无玩家参考仍 pad=previous 链写实病板。
必须保持：
1) converge start 调 assert_no_silent_prior_asset_reuse：goal/refs 含 assets/skill_*、sheet_session_、merge_phase1、relation.md 且无接续词则拒；
   assets/refs 布局垫图放行；
2) merge.* 且无 style_ref 时禁止 pad=previous；上轮 defects/next_fix 命中写实/产品静物等则纯文重开不垫板。
入口：cmd_converge start；_resolve_pad_auto。
适用：所有 converge start；merge 禁垫仅无玩家风格/格子参考时。
