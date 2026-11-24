---
id: 01M872VZPM5HYP75HHXXZE9JZR
module: feature.SkillsKit.Converge
entity: SlotLiveness
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/parallel_slots.py#list_active_sessions
- skills_kit/parallel_slots.py#write_heartbeat
- skills_kit/parallel_slots.py#isolate_corrupt_session
- skills_kit/converge.py#abort_prepare_session
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 槽位看心跳和损坏隔离，不看文件修改时间
verify: unittest tests.test_delivery_speed.TestStaleSlots tests.test_parallel_reserve.PrepareAbortTests.test_abort_clears_only_the_matching_active_pointer
  -q
applies: 并行槽计数、prepare 失败收尾、Hook 刷新心跳时
aliases:
- mtime
- 损坏会话
- prepare_aborted
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：过期只看会话文件 mtime，长时间等模型会被当成失联；损坏的 JSON 被 continue 跳过，等于没占槽。prepare 失败也不清活动索引。
必须保持：
1. 新鲜度看 heartbeat_at 或 _heartbeats 侧车，状态分 generating / waiting_model / awaiting_human / lost。
   lost 或不新鲜才不占槽。
   不把 mtime 当运行状态。
   没有心跳时才退回 started_at。
   过期不改会话 JSON。
2. JSON 解析失败或不是对象：把文件隔离到 _corrupt，写 hold 和 log.jsonl，继续占槽。release_corrupt_slot 在人工确认或恢复后才放开。
3. prepare 确认本次 started_at 仍匹配并标成 prepare_aborted 后，按同一 session_id 和 started_at 摘掉活动索引。启动时间已经变了的后一次会话不动。
入口：skills_kit/parallel_slots.py list_active_sessions；skills_kit/converge.py abort_prepare_session。
