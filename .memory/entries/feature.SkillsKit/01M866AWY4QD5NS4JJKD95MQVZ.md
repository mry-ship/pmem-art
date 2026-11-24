---
id: 01M866AWY4QD5NS4JJKD95MQVZ
module: feature.SkillsKit
entity: IdentityFromPlay
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_icon_a_game_read_issues
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 命名了游戏就要先写玩法，禁止收成徽章或摆件
verify: unittest tests.test_reasonableness_gate.TestReview.test_icon_a_game_badge_fails
  tests.test_reasonableness_gate.TestReview.test_icon_a_game_play_may_drop_invented_anchors
  tests.test_reasonableness_gate.TestReview.test_icon_a_match3_blank_stack_fails -q
applies: icon.a 合理性，草稿或修订句点了游戏、三消、配牌、tile match 或 match-3
aliases:
- 让人认出
- 徽章
source:
  kind: conversation
---
需求来源：跑桌面图标反向发现，执行者把玩家命名的游戏收成自造物件，合理性闸用草稿锚点把这个物件锁死。随后把「三消必须画成一枚牌」写进总闸，游戏又被收成一枚徽章。
必须保持：命名了游戏的 icon.a，修订句要有「让人认出」或「玩法是」，英雄要体现相同、配成、一组、多张或角色半身。
叠塔摆件失败。
一枚星、一枚牌、一枚徽章失败。
写明玩法之后，草稿里自造的叠塔和颗星锚点可以丢掉。
闸门不指定某一款游戏必须画成哪一个物件。
9.5 不降。
适用：icon.a 合理性；草稿或修订句点了游戏、三消、配牌、tile match 或 match-3。
入口：skills_kit/reasonableness_gate.py 的 _icon_a_game_read_issues；共享合理性步骤在 skill_specs。
