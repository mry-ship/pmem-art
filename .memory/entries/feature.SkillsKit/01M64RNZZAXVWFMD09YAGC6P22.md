---
id: 01M64RNZZAXVWFMD09YAGC6P22
module: feature.SkillsKit
entity: StopFollowupScope
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/converge_loop.py
revision: git:e7ad1e7
author: yanghu
note_date: '2026-10-30'
summary: stop followup禁止打进非出图对话窗
verify: python3 -m unittest tests.test_converge_loop -v 含 test_stop_hook_does_not_hijack_other_conversation
applies: Cursor 多对话并行且本仓装了 pmem-art stop hook 时
source:
  conversation: 91c058f7-a82a-4700-bc33-06d0c5543085
---
现象：出图后 Cursor stop hook 用 followup_message 自动续跑「第N轮还没审图」，会挤占本来有别的任务的 Composer 窗口并抢走焦点。
根因：.memory-art/converge/_active.json 是项目全局的；任意对话 stop 都会读到未完成的 converge 并注入 followup。
排除：继续用全局 active 无差别地发 followup_message。
正确做法：_active 绑定 owner_conversation_id；pre-gen 认领出图对话；stop 仅当 conversation_id 与归属一致才发 followup；错窗静默放行。
同窗内 followup 续跑仍保留（闭环不能停）；Cursor 同窗唤醒抢焦点是 IDE 侧已知问题，本仓只能避免错窗劫持。
