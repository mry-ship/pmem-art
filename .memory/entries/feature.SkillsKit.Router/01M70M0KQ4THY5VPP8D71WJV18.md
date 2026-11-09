---
id: 01M70M0KQ4THY5VPP8D71WJV18
module: feature.SkillsKit.Router
entity: RouteGateConcurrent
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/route_gate.py#save_route_advise
- skills_kit/route_gate.py#load_route_advise
- skills_kit/route_gate.py#goal_matches_route_text
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: conversation 分槽读写隔离；goal 同题扩写放行
verify: python3 -m unittest tests.test_route_false_fire -q
applies: 多对话/多技能并发 route + converge start
---
需求来源：全技能并发展陈时 last_advise 互相覆盖，且开画 goal 长于 route 原文被闸误拦。
必须保持：带 conversation_id 的 save 只写 by_conversation；
load 有 cid 无分槽 fail-closed 不回落全局；
goal_matches_route_text 允许 route⊆goal 同题扩写，换题仍拦；
无 conversation 的全局写法不变。
入口：skills_kit/route_gate.py。
