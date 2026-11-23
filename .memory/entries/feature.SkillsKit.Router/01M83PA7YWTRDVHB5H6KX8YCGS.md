---
id: 01M83PA7YWTRDVHB5H6KX8YCGS
module: feature.SkillsKit.Router
entity: PromptWriteIntent
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_wants_prompt
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: prompt 意图收别生图与提示词方案
verify: tests.test_route_advise.RouteAdviseTests.test_prompt_scheme_bie_sheng_tu_not_ordinary
applies: 未点名 /pmem-prompt 但口语要提示词且本步不生图
source:
  kind: conversation
---
需求来源：全技能展陈 prompt.write 路由落到普通图。
必须保持：含提示词/brief/prompt 且命中 别生图/不生图/提示词方案/先不出图/写提示词 等时 route_ids=prompt.write，banner 按提示词而非【走默认路径】普通图。
入口：plan_route/_wants_prompt。
