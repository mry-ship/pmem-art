---
id: 01M64G4CRN8H84WS1HQ4N3XTCQ
module: infra.Cli
entity: StopReminder
kind: feature
status: active
supersedes:
- 01M64F0QTZPDZ8ECT73PQHMNQK
anchors:
- .memory/config.yaml
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 本仓打开gate.stop_reminder，关analysis_reminder
verify: grep stop_reminder .memory/config.yaml 为 true；analysis_reminder 为 false
applies: 本仓库 Cursor 会话结束催记行为
aliases:
- 本轮修改了
- stop_reminder
- 功能记录催记
source:
  conversation: c5fffe7a-eb5a-4d26-9184-a63d279a801c
---
需求来源：用户 2026-10-30 要求 stop_reminder 开（true）、analysis_reminder 关（false）。
必须保持：`.memory/config.yaml` 里 `gate.stop_reminder: true`（改了模块没写功能记录 → 结束催「[pmem] 本轮修改了…」）；
`gate.analysis_reminder: false`（只查记忆未改代码时不催）。
`gate.mode` 仍为 block；`question_review` / `read_digest` 保持 true。
推翻此前「本仓关闭 stop_reminder」的功能记录。
