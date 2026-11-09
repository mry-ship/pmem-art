---
id: 01M70V8DMXNBGNPWK5JTWD5C65
module: feature.SkillsKit
entity: StyleSourcePriority
kind: decision
status: active
supersedes:
- 01M6NCXGJN5YBSMAD89N4RS5D2
anchors:
- skills_kit/install.py#_render_agent_doc_block
- skills_kit/skill_specs.py
- docs/COMMERCIAL_BENCHMARK.md
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 风格优先级：文字>参考>品类默认；merge默认钉Merge Mansion
verify: rg 开跑风格优先级 skills_kit/install.py；rg '仅 merge 品类钉 Merge Mansion' .cursor/skills/pmem-draw/SKILL.md；python3
  -m unittest tests.test_skill_router -q
applies: 开跑选风格；普通图/原画/UI/图标A·C/合成梯/提示词；有文字或风格参考时不适用品类默认
aliases:
- 风格优先级
- 缺风格默认
- Merge Mansion默认
---
为什么：冰淇淋合成梯偏写实，根因是缺省三家并列未钉死、文字/参考优先级不清。
做法：文字>风格参考>品类默认；有文字+构图/整表参考时参考只锁版式；休闲 merge 缺省只钉 Merge Mansion。
排除：三家并列未选定；非 merge 一律套软塑胶；有文字仍锁参考画风；开场0无条件强制软塑胶；benchmark 半成品默认链。
代价：链型对标仍可用 Travel Town 真档序，渲染缺省名固定 Merge Mansion。
入口：install §6、各技能执行卡、COMMERCIAL_BENCHMARK、merge_cabinet.yaml。
