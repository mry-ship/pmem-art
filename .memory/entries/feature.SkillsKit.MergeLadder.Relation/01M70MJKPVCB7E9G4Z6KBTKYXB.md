---
id: 01M70MJKPVCB7E9G4Z6KBTKYXB
module: feature.SkillsKit.MergeLadder.Relation
entity: MergeCasualLadderContract
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- docs/MERGE_MULTI_LENS.md
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 主流merge档序是完整SKU换代；半成品仅建造/修复
verify: grep 朴素完整小件 skills_kit/skill_specs.py；grep 半成品/骨架句式仅限 docs/MERGE_MULTI_LENS.md
applies: /pmem-merge-ladder 定链
verified: '2026-11-10'
verified_at: '2026-11-10T16:07:00.985+08:00'
---
画师质疑默认「原料→半成型→完整件」。
对照 Merge Mansion/Travel Town：清洁工具、洗涤剂、植物等主流链每档已是完整货柜件，只是形态换代；
原料/骨架/半成品只属于建造组装或碎片修复过程类型。
必须保持：技能默认句式改为「朴素完整小件→换代完整件→…→犒赏」；
禁止把半成品流水线套到主流 shop_ladder。
