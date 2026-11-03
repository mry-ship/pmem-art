---
id: 01M6EBG7J4VPZJK15BM1RN1GSJ
module: feature.SkillsKit
entity: MergeChainMode
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#judge_relation_rows
- skills_kit/merge_relation.py#parse_rows
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-02'
summary: 合成梯支持 chain_mode/levels6|8/shop叙事闸
verify: python -m unittest tests.test_merge_relation.MergeRelationTests.test_shop_ladder_levels_six_needs_evolve_and_why
applies: pmem-merge-ladder 关系 yaml 与 relation-judge；玩家点名六档或同店升级时
---
需求来源：节日五链整表迭代失败——默认 same_object+base_body 把升级画成「同一母体焊小饰片」，机读过关但叙事不通；玩家明确允许换相关物件、不必每档保留 L1 原件。

必须保持的行为：
1. 默认轻门（不写 chain_mode）仍按 MergePerCell：不强制 family/merge_why；parts_add 具体；可选 base_body。
2. chain_mode=same_object 时必须 base_body，且 silhouette/name 留母体词。
3. chain_mode=shop_ladder|species_change 时禁止 base_body；要求 evolve_to 不重复、L2+ merge_why 具体（禁「更华丽」等空话）；parts_add 可不填。
4. levels 仅 6 或 8；门禁按 N 行审，禁止为凑 8 硬补无意义档。
5. overview_sheet 为交付选项，不改变默认 per_cell；整表禁止垫对方模型成图做「公平对比」。

适用条件：pmem-merge-ladder 关系 yaml / relation-judge；玩家点名 1–6 档或同店升级时。

入口：skills_kit/merge_relation.py 的 parse_rows / judge_relation_rows；
`.agents|.cursor|.claude/skills/pmem-merge-ladder/SKILL.md`。
