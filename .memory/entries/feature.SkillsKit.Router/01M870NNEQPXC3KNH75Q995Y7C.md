---
id: 01M870NNEQPXC3KNH75Q995Y7C
module: feature.SkillsKit.Router
entity: ExpressionKeepAsk
kind: feature
status: active
supersedes:
- 01M86ZYWRJVH6YSYWVCG2B9XWJ
anchors:
- skills_kit/agent_router.py#_expression_keep_ask
revision: git:ff5f930
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 带图改表情又要求其余保持时先问，不开克隆
verify: unittest tests.test_route_false_fire.RouteFalseFireTests.test_expression_keep_with_image_asks_not_clone
  tests.test_route_false_fire.RouteFalseFireTests.test_variant_huancheng_stays_variant
  -q
applies: 带原图或口头垫图，改表情又要求其余保持时
aliases:
- False Execute
- expression_keep
source:
  conversation: 7f9cd1bd-0998-40af-b6c9-8c432eb321b3
---
需求来源：带原图说「把这只猫改成惊讶的表情，其他保持不动」会直接开克隆，属于 False Execute。
必须保持：有原图或口头垫图，且「改成/换成/变成 + 表情词」又要求其余保持时，reason=expression_keep，不开画，execute_ok 为假，不进 draw.clone。先问局部改还是变体。
点名「走变体」且有同一身份仍是变体。没有原图仍可走变体。「变成微笑的猫」没有保持句仍是克隆。
入口：plan_route / pmem_art.py route。
