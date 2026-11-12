---
id: 01M758H5AF4VPNYCBR0T8EHVT0
module: infra.Cli
entity: StopFollowupScope
kind: correction
status: active
supersedes:
- 01M756TSW89Z0K0P01ZJAB4NZA
anchors:
- pmem_art.py#cmd_hook
- skills_kit/converge_loop.py#claim_active_conversation
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 认领只走 post-asset；pre-gen 永不认领
verify: unittest tests.test_converge_loop.TestConvergeLoop.test_pre_gen_generate_image_does_not_claim_owner
  tests.test_converge_loop.TestConvergeLoop.test_post_asset_generate_image_claims_owner
  -q
applies: Cursor GenerateImage 出图后 stop 续跑闭环时
aliases:
- pre-gen 不认领
- 只 post-asset 认领
verified: '2026-11-11'
verified_at: '2026-11-11T21:41:56.506+08:00'
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
上一版仍写「手工挂上 pre-gen 时仍可认领」。
玩家要求去掉这条双路径：指不定上下文绑错就难纠正。
更正：claim_active_conversation 只在 post-asset + 真 GenerateImage + 有活跃 converge 时执行；
pre-gen 即使手工挂上也不认领；
Write/Edit/MCP/pre-tool 不认领。
stop 仍仅 owner 一致才 followup。
