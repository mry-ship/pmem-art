---
id: 01M64EJX5YHFHCY6R090XFC0A2
module: infra.Scripts
entity: StopThresholdFallback
kind: feature
status: active
supersedes: []
anchors:
- scripts/build_v8_20_skill_html.py
- scripts/rerun_homepage_1029_loop.py
- benchmark_evolution.py
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 批跑脚本缺threshold时回退必须是9.5，不得写死旧9.6
verify: rg \"or 9\\.6|TH = 9\\.6|--threshold\\\", \\\"9\\.6\" scripts benchmark_evolution.py
  无产品停机回退命中
applies: 展陈重跑、V8/Grok 批跑、homepage rescored 脚本
aliases:
- 批跑阈值
- or 9.5
source:
  conversation: 3551449c-c43f-4703-8575-43749b09f5ba
---
需求来源：停机线改为 9.5 后，展陈重跑/V8 批跑脚本里大量 `or 9.6`、`TH = 9.6`、`--threshold 9.6` 会让看板与 harness 仍按旧线展示或判断达标，与 skills_kit 合同分叉。
必须保持：scripts 与 benchmark_evolution 在 manifest/state 未给 threshold 时回退 9.5（或导入 DEFAULT_THRESHOLD）；
显式传给 converge 的 --threshold 默认 9.5。
批跑仍不是 skill 合同真值（见 NotContract），但数字必须与现行 DEFAULT_THRESHOLD 对齐。
入口：scripts/build_v8_20_skill_html.py、build_v8_20_skill_v2fix_html.py、build_skill_look_board.py、run_v8_20_skill_converge_grok.py、_grok_batch_helper.py、rerun_homepage_1029_loop.py、benchmark_evolution.py。
