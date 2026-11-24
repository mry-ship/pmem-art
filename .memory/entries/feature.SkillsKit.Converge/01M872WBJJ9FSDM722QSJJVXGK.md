---
id: 01M872WBJJ9FSDM722QSJJVXGK
module: feature.SkillsKit.Converge
entity: SlotLiveness
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/parallel_slots.py#list_active_sessions
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 不能用文件 mtime 判断会话还在跑，也不能把坏 JSON 当成没占槽
verify: unittest tests.test_delivery_speed.TestStaleSlots -q
applies: 改并行槽过期或坏会话计数时
aliases:
- mtime
- 损坏会话
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
排除：list_active_sessions 用 p.stat().st_mtime 超过 36 小时就跳过；JSON 解析失败直接 continue。
等模型或外部任务卡住时文件不一定被改写，mtime 会把还在跑的会话放掉。坏文件被跳过则并行槽少算一个。
正确做法：心跳时间与 generating / waiting_model / awaiting_human / lost；坏文件隔离进 _corrupt 并继续占槽，等人确认后再 release_corrupt_slot。
