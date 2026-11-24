---
id: 01M863GQDVXF3YY9PC5YGDJ6XC
module: feature.SkillsKit.Icon
entity: IconAGameRead
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_icon_a_game_read_issues
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 三消图标必须是一枚可配牌面，空白叠塔过不了闸
verify: unittest tests.test_reasonableness_gate.TestReview.test_icon_a_match3_blank_stack_fails
  tests.test_reasonableness_gate.TestReview.test_icon_a_match3_single_tile_may_drop_stack_anchors
  tests.test_reasonableness_gate.TestReview.test_icon_a_match3_king_swap_still_fails
  -q
applies: icon.a 合理性 review，草稿或修订句点了三消、配牌、tile match 或 match-3
aliases:
- 叠塔
- 空白方块
- 三消图标
source:
  kind: conversation
---
需求来源：Tile Match 桌面图标被写成三块空白方块叠塔，合理性清单仍全部 ok。
必须保持：icon.a 的草稿或修订句出现三消、配牌、tile match、match-3 时，修订句必须是一枚超大牌面，并写明牌面或可配花色。
修订句里肯定出现的一叠、叠塔、三块、积木判失败。
改成合格牌面时，叠塔和颗星这两类草稿锚点不再算换题材；
游戏名锚点和其他题材的锚点丢失仍按原规则拦。
9.5、清单和垫图规则不降。
适用：icon.a 合理性 review。
入口：skills_kit/reasonableness_gate.py 的 _icon_a_game_read_issues；Mode A 正文在 skill_specs 的 A2。
