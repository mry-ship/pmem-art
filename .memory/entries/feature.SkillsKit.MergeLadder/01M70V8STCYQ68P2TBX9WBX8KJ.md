---
id: 01M70V8STCYQ68P2TBX9WBX8KJ
module: feature.SkillsKit.MergeLadder
entity: MergeStyleDefault
kind: feature
status: active
supersedes: []
anchors:
- .agents/skills/pmem-merge-ladder/SKILL.md
- skills_kit/skill_specs.py
- skills_kit/data/benchmarks/merge_cabinet.yaml
- docs/MERGE_MULTI_LENS.md
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 合成梯风格：文字优先；无文字跟参考；都无钉Merge Mansion
verify: rg '出图必须垫这张参考锁版式' .agents/skills/pmem-merge-ladder/SKILL.md；python3 -m unittest
  tests.test_skill_router.SkillRouterTests.test_install_keeps_one_command_per_skill
  tests.test_skill_hardening.BenchmarkTests.test_lookup_merge -q；pmem_art.py benchmark
  lookup --category merge 含 Merge Mansion 与朴素完整小件
applies: 跑 /pmem-merge-ladder；玩家未另点非merge画风时
aliases:
- 风格优先级
- Merge Mansion默认
- 缺风格默认
---
需求：画师明确风格来源优先级，并要求缺省只钉一个顶级休闲 merge。
必须保持：1)有文字风格跟文字（整表参考可只锁版式）；2)有参考无文字跟参考表面；3)无参考按文字取风格；4)都无时 surface 默认钉 Merge Mansion 货柜软塑胶，不三家并列。
开场0垫图不得无条件强制软塑胶画风；benchmark merge_cabinet 档序为完整SKU形变非原料空壳。
适用：合成梯开跑写 surface / vibe。
入口：/pmem-merge-ladder 风格优先级；docs/COMMERCIAL_BENCHMARK；benchmark lookup --category merge。
