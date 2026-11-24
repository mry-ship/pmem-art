---
id: 01M86SJA4TQAHTX7CCE7XZYNGH
module: feature.SkillsKit.Router
entity: LayerSplitRoute
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#plan_route
- skills_kit/route_normalize.py#wants_layer_split
- skills_kit/route_gate.py#_layer_blocks_converge
- skills_kit/agent_route_cases.py#build_cases
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 拆图层语句落到 layer.split 且可放行；开画闸拒绝走 converge
verify: unittest tests.test_route_false_fire.RouteFalseFireTests.test_layer_split_can_pass_route_but_not_converge
  test_layer_split_does_not_steal_neighbors -q
applies: 改拆图层口语、路由话术库或开画闸时
aliases:
- 拆图层
- 分图叠回
- layer.split
- pmem-layer-split
source:
  conversation: 8434809b-e30b-410f-9267-50d21ac61575
---
需求来源：技能逻辑链体检与复查。
必须保持：「拆图层 / 分图叠回 / 装修分块 / 背景一份其余若干份 / 装修槽位或变身槽位再加拆、叠回或切块 / 成词 layer split」以及 /pmem-layer-split 返回 route_ids=[layer.split]。
装修槽位单独出现、「背景一份，其他留给标题」、layer splitting 仍是普通图。
话术库须有拆图层原型，否则近邻不一致会把 execute_ok 打成 false，清楚口语也开不了画。
开画闸：当前 goal 只路由到 layer.split，或上次缓存只有 layer.split 时，拒绝 converge start，改走定块、隔离、叠回。
标准句里的「不生图」不能被当成还要出验证图。
「全部重跑」默认九支仍不自动加入拆图层。
入口：plan_route、wants_layer_split、check_route_gate、advise_route。
