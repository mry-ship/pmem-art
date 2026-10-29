---
id: 01M642X3CDJ59AEAKBDH897HSQ
module: infra.Tests
entity: NegationLock
kind: exclusion
status: seed
supersedes: []
anchors:
- skills_kit/prompt_scale.py#find_affirmative_lock_hits
- tests/test_param_validation.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 否定句不能当成构图或垫图的肯定锁
verify: find_affirmative_lock_hits('勿写锁死构图，禁止垫图一致性高') 为空
aliases:
- 否定锁
---
依据 test_param_validation：含「勿/禁止/不要」的句子不能当成肯定锁。排除：把「勿写锁死构图」解析成锁死构图。否定句不当锁。
