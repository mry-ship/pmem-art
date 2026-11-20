---
id: 01M7WNBB7EPRBVMYY10Y24SYHQ
module: infra.Scripts
entity: NotVisualProof
kind: exclusion
status: active
supersedes:
- 01M642X4H1C0ZVG4B4N8EBYF5W
anchors:
- benchmark_evolution.py
- docs/BENCHMARK_LAYERS.md
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 禁止把evolution剧本分当成视觉进化证据
verify: docs/BENCHMARK_LAYERS.md；benchmark 头注释含 B1 SYSTEM
applies: 写进化报告或引用 benchmark_evolution 时
aliases:
- 剧本分
- 假进化
- B1
source:
  conversation: c8eef2a3-73d7-46b8-850d-eeac1e85ee27
---
现象：benchmark_evolution 用程序化PNG + 写死 score/defects 灌 converge。
排除：把该 harness 分数曲线写成「记忆让画质变好」。
允许：报 CLI/记忆条数/Warm-Start/红线写入。
视觉实证走 B2。与 NotContract（批跑非skill合同）并列，互不替代。
