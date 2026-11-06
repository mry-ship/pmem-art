---
id: 01M6RECJ7W8SFXSHV43Y86N85T
module: feature.SkillsKit
entity: MergeSheetCenter
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#split_sheet_grid
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 整表切格每格只居中一次
verify: py -3 -u -m unittest tests.test_merge_relation.MergeRelationTests.test_split_sheet_centers_each_cell_once
  -q
applies: 合成梯整表切成 8 格方图时
aliases:
- 切格
- 二次居中
source:
  conversation: 2fb9d6ff-529d-4817-aa0f-d09fd39d062b
---
split_sheet_grid 原先对同一格调两次 cell_to_equal_square。
第二次会把已经摆正的方图再按主体占比缩一遍，构图被挪走。
现在每格只居中一次。
工作树 quizzical-hugle 里口语折叠、注册表和技能正文已改回与主目录一致，避免「以后按这张画」被折掉、总控说明被写短。
