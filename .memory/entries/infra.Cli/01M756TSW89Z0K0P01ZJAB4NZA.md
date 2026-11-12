---
id: 01M756TSW89Z0K0P01ZJAB4NZA
module: infra.Cli
entity: StopFollowupScope
kind: correction
status: active
supersedes:
- 01M64RP34BNSK8Q8MS1SAC4XFX
anchors:
- pmem_art.py#cmd_hook
- skills_kit/converge_loop.py#claim_active_conversation
- skills_kit/converge_loop.py#followup_allowed_for_conversation
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 关 pre-gen 后改由 post-asset 认领出图窗
verify: unittest tests.test_converge_loop.TestConvergeLoop.test_post_asset_generate_image_claims_owner
  -q
applies: Cursor GenerateImage 出图后 stop 续跑闭环时
aliases:
- post-asset 认领
- stop followup 认领
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧功能要求仅 pre-gen + 真 GenerateImage 才 claim_active_conversation；
pre-gen 默认关闭后 owner 常空，Cursor stop 因 owner 空不发 followup，闭环续跑哑火。
更正：默认认领改走 post-asset（GenerateImage 成功后）；手工挂上 pre-gen 时仍可认领；Write/Edit/MCP/pre-tool 仍不认领；须已有活跃 converge session。
stop 仍仅 owner 一致才 followup；owner 空的 Cursor 窗静默。
记忆并入仍只靠 converge generate（已过滤 Warm-Start），不靠 Hook 灌提示词。
