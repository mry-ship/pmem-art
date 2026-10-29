---
id: 01M64RP34BNSK8Q8MS1SAC4XFX
module: infra.Cli
entity: StopFollowupScope
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py
revision: git:7101334
author: yanghu
note_date: '2026-10-30'
summary: stop hook按conversation_id归属才发followup
verify: python3 -m unittest tests.test_converge_loop -q
applies: Cursor stop/pre-gen hook 触发 pmem_art.py hook 时
aliases:
- 抢窗
- 错窗催办
- followup_message
- 还没审图
source:
  conversation: 91c058f7-a82a-4700-bc33-06d0c5543085
---
需求来源：出图后「还没审图」催办挤占别的任务窗口。
必须保持：
1) cmd_hook stop 仅当 conversation_id 与 _active.owner_conversation_id 一致时输出 followup_message；错窗与 owner 空的 Cursor 窗静默放行。
2) 无 conversation_id（勿把 host session_id 当 conversation_id）时仍允许 followup（CLI/旧主机）。
3) 仅 pre-gen + 真 GenerateImage（含嵌套 toolName）才 claim_active_conversation；Write/Edit/MCP/pre-tool 不认领。
入口：skills_kit/converge_loop.py#followup_allowed_for_conversation、claim_active_conversation；
pmem_art.py#cmd_hook、#hook_conversation_id、#is_generate_image_tool。
