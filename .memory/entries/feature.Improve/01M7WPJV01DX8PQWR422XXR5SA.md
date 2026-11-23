---
id: 01M7WPJV01DX8PQWR422XXR5SA
module: feature.Improve
entity: MemoryTrust
kind: correction
status: archived
supersedes: []
anchors: []
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: candidate堆积只计显式trust=candidate的active
verify: unittest tests.test_art_doctor_ext -q
applies: doctor 打印记忆trust堆积时
aliases:
- candidate堆积
superseded_by: 01M80TRUSTFIXGRANDFATHER
---
复查doctor：原先entry_trust把provisional也算candidate，导致堆积虚高。
更正：check_candidate_backlog只计status非provisional且frontmatter显式trust=candidate的条目；
无trust的旧active仍按verified祖父，不进promote队列提示。
（2026-11-23：后半句祖父条款已废，见 01M80TRUSTFIXGRANDFATHER。）
