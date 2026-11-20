---
id: 01M7WS31JA2XQZRRREGQDSQM3M
module: feature.Improve
entity: MemoryTrust
kind: conclusion
status: active
supersedes: []
anchors:
- feedback.py#cmd_feedback
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: inbox反馈写条目必须带trust，缺参会TypeError
verify: unittest tests.test_memory_safety.TestInboxTriage -q
applies: feedback 写 .memory-art 条目或改 write_memory_entry 签名时
---
现象：加 trust 字段后，cmd_feedback 无模块 inbox 路径直接调 _write_memory_entry_unlocked 漏传 trust，单测 TestInboxTriage 报 TypeError。
修法：inbox 写入显式 trust=candidate；
_write_memory_entry_unlocked 给 trust/proj_* 默认值防再漏。
