---
id: 01M787NX0RSHA7WPAWF8K993JM
module: feature.SkillsKit.Converge
entity: StyleStripPadAspect
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/validate_params.py#_is_style_surface_strip
- skills_kit/validate_params.py#validate_case_generation_params
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 横条货条只锁画风；显式交付画幅不因方向翻车拦截
verify: python -m unittest tests.test_delivery_gates.DeliveryGateTests.test_style_strip_pad_allows_square_delivery
  tests.test_delivery_gates.DeliveryGateTests.test_portrait_pad_cannot_be_filled_into_landscape
  -q
applies: converge 参数校验遇横条风格垫 + 显式方/竖交付画幅时
aliases:
- food_strip
- 横条货条
- 不能加边填成
source:
  conversation: 679ccb52-31d7-4ad3-8b43-02f24338f778
---
需求来源：图标/方图交付垫 GH food_strip（如 1330×405）时，校验试图加边填成 1:1 触发「不能加边填成」硬拦。
必须保持：主垫名含 _strip/food_strip 或宽高比≥2.4 的极宽货条，且与目标 aspect 方向冲突时，只作画风参考、不强制几何加边；多垫图时优先把方向匹配的提到主垫。普通竖/横几何垫图方向冲突仍硬拦。
入口：skills_kit/validate_params.py validate_case_generation_params / ensure_aspect_matched_ref。
