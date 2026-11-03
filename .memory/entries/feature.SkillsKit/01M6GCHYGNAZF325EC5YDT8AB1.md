---
id: 01M6GCHYGNAZF325EC5YDT8AB1
module: feature.SkillsKit
entity: MergeChainMode
kind: correction
status: active
supersedes:
- 01M6EBG7J4VPZJK15BM1RN1GSJ
anchors:
- skills_kit/merge_relation.py#_track_levels
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: levels允许6|8|9|12|15；整表参考强制overview不改无信号时的per_cell默认
verify: python -m unittest tests.test_merge_relation -q
applies: pmem-merge-ladder 关系 yaml 与 relation-judge
---
更正 MergeChainMode 功能记录中「levels仅6或8」：整表参考常见3×3/4×3/5×3，机读现允许6|8|9|12|15。
overview_sheet在有格子参考或「一起出」时强制，仍不改变「无整表信号时默认per_cell」（MergePerCell）。
一组X未说同模加零件走species_change/shop_ladder。
