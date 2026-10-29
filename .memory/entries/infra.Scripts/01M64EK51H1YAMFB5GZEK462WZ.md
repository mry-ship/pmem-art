---
id: 01M64EK51H1YAMFB5GZEK462WZ
module: infra.Scripts
entity: HardcodedThresholdDrift
kind: risk
status: active
supersedes: []
anchors:
- scripts/build_v8_20_skill_html.py
- scripts/run_v8_20_skill_converge_grok.py
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 批跑硬编码旧停机数字会在skills_kit改阈值后悄悄分叉
scope: project
verify: 改阈值后 rg \"or 9\\.[0-9]\" scripts 与 DEFAULT_THRESHOLD 对照
applies: 改停机线或批跑看板生成时
aliases:
- 字面回退
- 阈值分叉
source:
  conversation: 3551449c-c43f-4703-8575-43749b09f5ba
---
看代码不易一眼看出：scripts 里 `state.get("threshold") or 9.6` 这类字面回退不走 DEFAULT_THRESHOLD。
skills_kit 把停机线改成 9.5 后，批跑 HTML/达标判断仍可能按 9.6 展示或比较，造成「合同已 9.5、看板还写 9.6」的假象。
约束：改 DEFAULT_THRESHOLD 时必须扫 scripts/benchmark 的字面回退；优先 import DEFAULT_THRESHOLD，避免再写死小数。
不影响：历史 converge 会话里当时记录的 target_score_threshold。
