---
id: 01M872JN09ZCJSSMMXC4KM5XKS
module: feature.SkillsKit.Converge
entity: ActiveIndex
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge_loop.py#mark_active_session
- skills_kit/converge_loop.py#loop_followup
- skills_kit/converge_loop.py#claim_active_conversation
- pmem_art.py#cmd_hook
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 活动会话按 session 和 conversation 分别登记，不用全局单指针
verify: unittest tests.test_converge_loop -q
applies: 同一仓库并行多个 converge 会话，且 Hook 要按对话催办时
aliases:
- _active.json
- 活动指针
- follow-up
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：并行槽可以同时有多个会话，但 _active.json 只存一个 session_id 和 owner_conversation_id。后启动的会话会盖掉活动指针，Hook 催办也只能找到最后那一个。
必须保持：_active.json 是索引。sessions 按会话号记归属对话，conversations 按对话号回指会话。标记新会话不删掉其他会话的归属。
stop / pre-gen 带 conversation_id 时只解析这个对话的会话。没有对话号时，只有索引里正好一个会话才回退到它。
claim 只绑定唯一一个还没有归属的会话，不抢别的对话已经占住的会话。finish 只摘掉这一个会话。
入口：skills_kit/converge_loop.py mark_active_session / loop_followup；pmem_art.py stop 与 post-asset。
