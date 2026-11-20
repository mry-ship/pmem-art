---
id: 01M7WNARSNBEWTYV25K2F177GQ
module: feature.Benchmarks
entity: LayerContract
kind: feature
status: active
supersedes: []
anchors:
- docs/BENCHMARK_LAYERS.md
- benchmarks/b2_visual_bench.py
- benchmark_evolution.py
- lifecycle.py#collect_doctor_summary
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: B2支持VLM打分assemble与empirical退化对比
verify: unittest tests.test_b2_visual_bench -q
applies: 跑B2真评或doctor视觉信号时
aliases:
- score-image
- assemble
---
需求来源：继续落地B2。
必须保持：--score-image经独立VLM写b2_results.jsonl；
--assemble仅在全是empirical行时写empirical=true；
doctor只对empirical基线报B2退化。
禁止allow-agent-fallback宣称进化。
入口：benchmarks/b2_visual_bench.py；
docs/BENCHMARK_LAYERS.md。
