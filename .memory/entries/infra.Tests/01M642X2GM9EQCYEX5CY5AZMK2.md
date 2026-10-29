---
id: 01M642X2GM9EQCYEX5CY5AZMK2
module: infra.Tests
entity: Session
kind: exclusion
status: seed
supersedes: []
anchors:
- tests/test_p2_session_and_aspect.py#test_generate_without_session_fails_and_does_not_create
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 没有converge start时generate必须失败，不能悄悄建会话
verify: tests.test_p2_session_and_aspect.GenerateWithoutSession
aliases:
- 静默建会话
---
依据 tests/test_p2_session_and_aspect.py：generate 在没有会话时必须失败，且不能悄悄创建 session 文件。
排除：为了让脚本跑通而让 generate 自动建会话。
没 start 就 generate 应失败。
