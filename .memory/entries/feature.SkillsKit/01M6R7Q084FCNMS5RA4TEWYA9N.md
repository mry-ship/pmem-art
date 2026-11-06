---
id: 01M6R7Q084FCNMS5RA4TEWYA9N
module: feature.SkillsKit
entity: AgentRoute
kind: risk
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_wants_style
- skills_kit/colloquial_lexicon.py#_style_lock_left
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 都按这张+画一张会误进锁风格后克隆
verify: plan_route('都按这张画一张窗边女孩', images=['a.png']).route_ids 应为 ['draw.ordinary']
applies: 改 _wants_style / colloquial 按这张折叠 / _style_verify_intent 时
---
未提交优化给 _wants_style 加了「都按这张」，口语折叠又用裸「都」保护不折成参考。
叠上 _style_verify_intent 见「画一张」就串克隆，导致「都按这张画一张窗边女孩」变成 style.lock→draw.clone，而「按这张画一张窗边女孩」仍是普通图。
锁风格触发应保留时间前缀（以后/往后），或要求色板/画风锁词且无具体新题材句。
