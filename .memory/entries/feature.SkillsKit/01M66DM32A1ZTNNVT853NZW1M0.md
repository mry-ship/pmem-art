---
id: 01M66DM32A1ZTNNVT853NZW1M0
module: feature.SkillsKit
entity: OrdinaryCanonSelfPoison
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_new_subject
- skills_kit/route_normalize.py#CANON_TEMPLATES
- skills_kit/route_normalize.py#infer_signals
revision: git:959a507
author: 1002378395@qq.com
note_date: '2026-10-30'
summary: 普通图标准句禁写「不换题材」；换题材须左非「不」
scope: project
verify: python -m unittest tests.test_route_advise.RouteAdviseTests.test_ordinary_canonical_does_not_self_poison_to_clone
  tests.test_route_advise.RouteAdviseTests.test_optimize_ref_with_ordinary_canonical_execute_ok
  tests.test_route_advise.RouteAdviseTests.test_bu_huan_topic_is_keep_not_clone -v
applies: /pmem-agent route 标准句二次规则与普通图/克隆分流
aliases:
- plan_conflict普通图
- 也不换题材误克隆
- 标准句自毒
source:
  conversation: aa0265fa-d1f5-45f9-b116-1b37f31766d0
---
现象：Agent 标准句「要画一张图；有参考也不换题材；走普通图」二次 plan_route 被判克隆，与原话普通图 plan_conflict，execute_ok=false，优化附图任务被闸门拦住。
根因：「换题材」子串命中「不换题材/也不换题材」；_new_subject / infer_signals 否定表只认「不要换」不认「不换」；普通图模板自带毒词。
更正：
  ① CANON_TEMPLATES 普通图改为「有参考；题材不变；
走普通图」；
  ② _new_subject 用 (?<![不])换题材 + keep 表含不换题材/题材不变；
  ③ route_normalize 同步；
  ④ 「走普通图」且无真换题材时 named_ordinary 优先于克隆。
旧模板句子现在也应判普通图（回归覆盖）。
