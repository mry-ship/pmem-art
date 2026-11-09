---
id: 01M6GCJZYKNH0PPAT1EA05ZXRZ
module: feature.SkillsKit.MergeLadder.Delivery
entity: MergeAtlasRef
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#_ALLOWED_LEVELS
- skills_kit/skill_specs.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 整表格子参考强制overview并垫图；levels扩到9/12/15
verify: python -m unittest tests.test_merge_relation.MergeRelationTests.test_overview_grid_levels_fifteen_allowed
  -v
applies: /pmem-merge-ladder 有整表格子参考或整表口语时
---
需求来源：乐器合成梯附船图格子参考时，Agent 仍走默认 per_cell+same_object 八档吉他，未数参考行列、未垫参考锁版式。

必须保持的行为：
1. 无整表信号时默认仍是 per_cell（MergePerCell）；轻门/chain_mode 规则不变。
2. 附图为多格白卡深底图集，或玩家说整表/一起出/参考咋出就咋出 → 强制 overview_sheet；先数行列；levels 跟格数。
3. levels 机读允许 6|8|9|12|15（对应常见 2×3/2×4/3×3/4×3/5×3）；audit 按 N 档而非写死 8。
4. 「一组 X / 多种 X」未说同模加零件 → species_change 或 shop_ladder；禁止默认同物件焊单母体。口味「禁止换物种」只约束 same_object。
5. 整表出图必须垫格子参考锁白卡/深底/间距/质感；不抄参考物件。整表白卡是版式，不是 per_cell 禁止的内嵌白底。

适用条件：/pmem-merge-ladder 有整表格子参考或整表口语时。

入口：skills_kit/skill_specs.py pmem-merge-ladder；
skills_kit/merge_relation.py _ALLOWED_LEVELS / audit_ladder_dir；
`.cursor|.claude|.agents/skills/pmem-merge-ladder/SKILL.md`。
