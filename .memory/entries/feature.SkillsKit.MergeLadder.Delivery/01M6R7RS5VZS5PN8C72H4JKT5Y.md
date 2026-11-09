---
id: 01M6R7RS5VZS5PN8C72H4JKT5Y
module: feature.SkillsKit.MergeLadder.Delivery
entity: MergeRelation
kind: risk
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#split_sheet_grid
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 整梯切格对同一格做了两次主体居中
verify: split_sheet_grid 每格只调用一次 cell_to_equal_square
applies: 整表 2x4 切成 L01-L08 时
---
split_sheet_grid 先 cell_to_equal_square(cell) 得到方图，保存前又对这张方图再跑一遍 cell_to_equal_square。
第二次会按新画布重新抽主体并缩放，多一次重采样，占位比例也可能被改。
应只保存第一次结果。
