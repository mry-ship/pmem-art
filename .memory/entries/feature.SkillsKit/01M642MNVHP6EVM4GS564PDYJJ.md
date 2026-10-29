---
id: 01M642MNVHP6EVM4GS564PDYJJ
module: feature.SkillsKit
entity: SplitOffset
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#cell_to_equal_square
- skills_kit/merge_relation.py#split_sheet_grid
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 花切顶和格里不居中是因为方卡铺在16:9行顶，不能按居中letterbox切
verify: python -m unittest tests.test_merge_relation.MergeRelationTests.test_cell_to_equal_square_centers_subject
applies: 16:9 组图按 2×4 切开成交货正方形
aliases:
- 花被切
- 不居中
- 内嵌方卡
---
花被切、展陈格里不居中的根因：模型在16:9上把圆角方卡铺在每行顶部，不是垂直居中的8个 letterbox 正方形。
按居中正方形切会切掉花顶；
按2×4整格 contain 会保住花，但主体贴左上、底下留灰。
内嵌方卡还会被当成主体，卡片本身歪在格子里。
必须按2×4取格后抽出真正物件，铺到平涂正方形正中再交货。
