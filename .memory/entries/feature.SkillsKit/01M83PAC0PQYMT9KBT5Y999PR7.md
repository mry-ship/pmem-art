---
id: 01M83PAC0PQYMT9KBT5Y999PR7
module: feature.SkillsKit
entity: StyleSurfaceOppositeAspect
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/validate_params.py#validate_case_generation_params
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 垫图方向与交付画幅相反时只锁画风
verify: tests.test_delivery_gates.DeliveryGateTests.test_portrait_pad_opposite_delivery_is_style_only
applies: validate_converge_params / converge start·generate 带垫图时
source:
  kind: conversation
---
需求来源：多图等显式 aspect 与竖垫冲突被硬拦。
必须保持：显式 aspect 与主垫方向相反时 style_surface_only=True、保留交付画幅、警告只锁画风；
同向仍可加边；
横条 strip 路径不变。
入口：validate_case_generation_params。
