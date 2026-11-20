---
id: 01M7WRV8H7C2N3DHM0KCRCKDWX
module: feature.Improve
entity: MemoryTrust
kind: conclusion
status: seed
supersedes: []
anchors:
- feedback.py#_write_memory_entry_unlocked
- feedback.py#cmd_feedback
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: inbox反馈写条目必须带trust，缺参会TypeError
verify: unittest tests.test_memory_safety.TestInboxTriage -q；pytest tests/test_memory_trust.py
  tests/test_art_doctor_ext.py -q
applies: feedback 写 .memory-art 条目或改 write_memory_entry 签名时
trust:
  status: candidate
  verification: unverified
version: 1
content_sha256: 68088e9226df2ec7c5bfbb2248acfaa63ed768690a959368037736fb44ae33b5
space:
  profile_id: project
  owner_id: ''
  project_id: Cursor-Pmem-Art
  module_id: feature.Improve
  entity_id: MemoryTrust
provenance:
  source_type: conversation
  source_id: ''
  extracted_by: ''
  recorded_by: 1002378395@qq.com
layer: memory
profile_id: project
profile_kind: conclusion
---
现象：加 trust 字段后，cmd_feedback 无模块 inbox 路径直接调 _write_memory_entry_unlocked 漏传 trust，单测 TestInboxTriage 报 TypeError。
修法：inbox 写入显式 trust=candidate；_write_memory_entry_unlocked 给 trust/proj_* 默认值防再漏。
公开 write_memory_entry 默认已是 candidate。
