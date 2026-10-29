---
id: 01M642MPPQBDD0TD9ECHV5P4CB
module: feature.SkillsKit
entity: GroupSheet
kind: decision
status: active
supersedes:
- 01M642JDW3E2Z3CRYSJCFKHWPA
anchors:
- skills_kit/merge_relation.py#split_sheet_grid
- skills_kit/merge_relation.py#cell_to_equal_square
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 整组16:9正方形格生成再切开，切后必须把主体铺到格心
verify: 组图按2x4切开后各档完整、主体居中、无内嵌方卡
applies: 关系讨论过关后的合成梯出图与展陈
aliases:
- 按组出图
- 2x4切格
---
仍选整组16:9（8个相同正方形格）交给生图模型再切开，为了锁同一机位、同一棚灯、同一画风管线；
共享的是镜头和灯，不是色相和材质。
切开后必须把主体抽到正方形正中（平涂格底），不能只 contain，也不能靠页面 CSS 居中。
展陈8档用4列两行，不要8列一行。
切进邻件或主体不在格心，那一档作废只重出那一档。
