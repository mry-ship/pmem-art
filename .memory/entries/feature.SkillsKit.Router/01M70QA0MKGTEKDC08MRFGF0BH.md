---
id: 01M70QA0MKGTEKDC08MRFGF0BH
module: feature.SkillsKit.Router
entity: RouteExpiredIdConflict
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/route_gate.py#check_route_gate
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 过期 route 与 route-id 冲突禁止静默换路由
verify: python3 -m unittest tests.test_route_false_fire.RouteFalseFireTests.test_expired_route_id_conflict_refuses_silent_reseed
  -q
applies: converge start / check_route_gate 遇过期分槽时
---
必须保持：本地路由过期且 named/expect route_id 不在缓存 route_ids 时 fail-closed，禁止用 --route-id 静默换路由；
须对当前话重跑 route。
conversation 分槽隔离仍成立。
入口：skills_kit.route_gate.check_route_gate。
