---
id: 01M758HBJP1JS5HV45H6SKMVXX
module: feature.SkillsKit.Agent
entity: StopFollowupScope
kind: correction
status: active
supersedes:
- 01M756VC66KZJQ23GDXTY75Z83
anchors:
- pmem_art.py#cmd_hook
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 出图窗认领只 post-asset，pre-gen 永不认领
verify: unittest tests.test_converge_loop.TestConvergeLoop.test_pre_gen_generate_image_does_not_claim_owner
  -q
applies: Cursor 多对话并行且本仓装了 pmem-art stop/post-asset hook 时
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
上一版仍写手工 pre-gen 可认领。
更正：只 GenerateImage post-asset 认领；pre-gen 永不认领。错窗静默、同窗 followup 续跑仍成立。
