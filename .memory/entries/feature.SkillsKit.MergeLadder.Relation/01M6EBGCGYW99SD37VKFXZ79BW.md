---
id: 01M6EBGCGYW99SD37VKFXZ79BW
module: feature.SkillsKit.MergeLadder.Relation
entity: MergeChainMode
kind: decision
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#judge_relation_rows
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-02'
summary: 默认轻门保留；shop_ladder才强制merge_why
applies: 关系门与技能开场必选
---
与 MergePerCell 对齐：默认不强制 merge_why。
仅 chain_mode=shop_ladder|species_change 启用 evolve_to+merge_why 叙事闸；
same_object 才强制 base_body。
overview_sheet 是交付选项，不改默认 per_cell。
