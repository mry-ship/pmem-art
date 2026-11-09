---
id: 01M6QR8DE3Y96BJ3ME26X7EBJY
module: feature.SkillsKit.Showcase
entity: RouteThreeFixes1106
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/colloquial_lexicon.py#_replace_once
- skills_kit/agent_router.py#_showcase_bare_icon
- skills_kit/agent_router.py#_non_art_ops
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 修锁风格折叠/展陈裸图标/非出图默认普通图
verify: pyw -3 -u -m unittest tests.test_route_false_fire tests.test_showcase_route
  -q
applies: 改口语折叠、展陈探针或默认兜底时
---
需求来源：审计三处路由洞后落地修复。必须保持：
  1) rewrite 不把「以后/都/往后…按这张」折成参考，「以后按这张画」→style.lock；
无样张 advise 仍 ask。
  2) 对比页裸「图标」+其它支 → icon_unspecified 停问，禁止只剩 merge 还执行；
「图标A+合成梯」两支都在。
  3) 检查技能/审计文档/单元测试/修 converge bug → unrecognized 停，不默认普通图。
适用：改口语折叠、展陈探针或默认兜底时。
入口：colloquial_lexicon._replace_once；
agent_router._showcase_bare_icon / _non_art_ops / _showcase_ids。
