---
id: 01M83P9HFQPRQD16PM6GABZGGW
module: feature.SkillsKit
entity: StyleSurfaceOppositeAspect
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/validate_params.py#validate_case_generation_params
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 显式交付画幅与垫图方向相反时只锁画风，不硬拦
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_portrait_pad_opposite_delivery_is_style_only
applies: converge start/generate 显式 aspect 与主垫方向不一致时
verified: '2026-11-23'
verified_at: '2026-11-23T16:38:52.743+08:00'
source:
  kind: conversation
---
竖垫+横交付（或多图机位垫与会话 aspect 相反）时 ensure_aspect_matched_ref 抛「不能加边填成」硬拦会话。
更正：捕获该 ValueError 后改 style_surface_only，保留显式 aspect_ratio，警告只锁画风；
同向仍可加边。
