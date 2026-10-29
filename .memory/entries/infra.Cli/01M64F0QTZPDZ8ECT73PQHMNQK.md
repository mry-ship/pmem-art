---
id: 01M64F0QTZPDZ8ECT73PQHMNQK
module: infra.Cli
entity: StopReminder
kind: feature
status: active
supersedes: []
anchors:
- .memory/config.yaml
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 本仓关闭gate.stop_reminder，不再催「本轮修改了」写记忆
verify: grep stop_reminder .memory/config.yaml 为 false；改模块后 stop hook 不再发「本轮修改了」
applies: 本仓库 Cursor 会话结束催记行为
aliases:
- 本轮修改了
- stop_reminder
- 催记
source:
  conversation: 3551449c-c43f-4703-8575-43749b09f5ba
---
需求来源：用户 2026-10-30 明确要求关掉 `[pmem] 本轮修改了…还没有写研发记忆` 这类 stop followup。
必须保持：`.memory/config.yaml` 里 `gate.stop_reminder: false`；
改代码后不再因未写功能记录自动追问。
`gate.mode` 仍为 block（改前仍须检索），`analysis_reminder` / `spec.reminder` 保持 false，`question_review` 仍可按需保留。
入口：.memory/config.yaml → gate.stop_reminder；实现见 pmem hooks reminders._pending_nudges。
