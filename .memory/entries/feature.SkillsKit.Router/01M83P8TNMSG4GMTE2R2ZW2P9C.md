---
id: 01M83P8TNMSG4GMTE2R2ZW2P9C
module: feature.SkillsKit.Router
entity: PromptWriteIntent
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_wants_prompt
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 提示词方案+别生图须走 prompt.write，禁止默认普通图
verify: unittest tests.test_route_advise.RouteAdviseTests.test_prompt_scheme_bie_sheng_tu_not_ordinary；route
  该句 route_ids=[prompt.write]
applies: 口语写提示词方案且本步不生图时
source:
  kind: conversation
---
展陈「写一套…提示词方案，别生图」被 _wants_prompt 漏检（只认「写提示词/先别画/先不出图」），近邻全是 prompt.write 仍落到 default 普通图 banner。
更正：_wants_prompt 增补 别生图/不要生图/不生图/提示词方案。
