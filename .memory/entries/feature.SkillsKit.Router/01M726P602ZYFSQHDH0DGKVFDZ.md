---
id: 01M726P602ZYFSQHDH0DGKVFDZ
module: feature.SkillsKit.Router
entity: RouteSkillSuite
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_skill_suite_request
- skills_kit/agent_router.py#_expression_swap_locked
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 全技能清点放行；换成惊讶仍走变体
verify: python -m unittest tests.test_route_false_fire.RouteFalseFireTests.test_all_skills_sentence_is_full_inventory
  tests.test_route_false_fire.RouteFalseFireTests.test_variant_huancheng_stays_variant
  tests.test_route_false_fire.RouteFalseFireTests.test_non_art_ops_stop_not_ordinary
  -q
applies: 总控认路。检查/审计技能实现仍是停，不进全清单
aliases:
- 全部跑一遍
- 换成惊讶
- 技能变体
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
现象：「把所有技能以及技能变体全部跑一遍」被「技能」当成查代码，路由停。变体原句里的「换成惊讶」让近邻把放行打成假。
必须保持：所有技能、全部技能、技能变体全部跑一遍，是全清单并且 execute_ok，不要因为支路超过 3 条或近邻不像而停。检查、审计、是否有问题仍停。
同一身份、换表情、走变体时，「换成惊讶」仍是变体。没有身份锁的「变成微笑的猫」仍是克隆。
入口：pmem_art.py route。
