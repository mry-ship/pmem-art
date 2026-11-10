---
id: 01M726N9ZADQMG2WJ0DAMN5Q5V
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: correction
status: active
supersedes:
- 01M70M0HCHB1MVWNK5KWHQTJRG
anchors:
- skills_kit/converge_policy.py#decide_round_stop
- .memory-art/config.yaml
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 安全早停默认关；打开后仍是 0.15/第2轮
verify: 'rg "safe_early_stop: false" .memory-art/config.yaml；python -c "from skills_kit.converge_policy
  import DEFAULT_SAFE_EARLY_STOP; assert DEFAULT_SAFE_EARLY_STOP is False"'
applies: 日常 converge。画师明确要开早停时再写 true
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
现象：2026-11-10 合成梯跑批仍出现 STOP_REGRESSION，喷壶第 3 轮 8.62 被退回 8.94。画师要求早停默认关闭。
旧结论 01M70M0HCHB1MVWNK5KWHQTJRG 把 safe_early_stop 改回 true，以此作废。
现状：缺省和项目 config 都是关。没有写成 true 时，掉分和平台不能在第 4 轮前停。到线仍是 ≥9.5，满 4 轮仍交最高分。
打开时仍用掉分 0.15、从第 2 轮起，不要改回 0.5/第 4 轮。
