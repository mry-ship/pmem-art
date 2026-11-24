---
id: 01M872WANC6ZVF6VMR4XC4TZEQ
module: feature.SkillsKit.Router
entity: ExpressionUncertain
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_expression_keep_ask
- skills_kit/agent_router.py#_keep_rest_signal
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 带图改表情拿不准是否保持其余时先问，不落克隆
verify: unittest tests.test_route_false_fire.RouteFalseFireTests.test_expression_keep_with_image_asks_not_clone
  tests.test_route_false_fire.RouteFalseFireTests.test_variant_huancheng_stays_variant
  -q
applies: 带原图改表情的路由
aliases:
- 其它保持
- expression_uncertain
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：其余保持只认了「其他/其余」，漏了「其它」和「其他地方尽量别变」。拿不准时会掉进普通图或克隆。
必须保持：带原图且在改表情时，肯定的保持句（含其它、尽量别变）走 expression_keep。只有软话（看着办、其他地方但没有明确保持）走 expression_uncertain，两种都先问局部改或变体。
「不用保持 / 别保持」这类否定不拦，仍可走克隆。点名走变体或局部改不拦。没有原图不拦。
入口：skills_kit/agent_router.py _expression_keep_ask / _keep_rest_signal。
