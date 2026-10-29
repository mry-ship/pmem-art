---
id: 01M64JKCF4ZZMJ3YV2HK20T5SS
module: feature.SkillsKit
entity: AgentRoute
kind: conclusion
status: active
supersedes:
- 01M64G8RFMYXYK67YQD0JQFWEN
anchors:
- skills_kit/route_normalize.py#normalize_for_route
- skills_kit/agent_router.py#_new_subject
- skills_kit/route_ask.py#detect_vague_ask
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 认路折叠禁灌extras；表情句末才抑换题材；软合成/图标停用人话问
scope: project
verify: unittest tests.test_artist_talk_accuracy tests.test_route_advise tests.test_agent_route_stability
  -q
applies: 口语认路与糊话 ask
aliases:
- 口语扩展
- COLLOQUIAL_EXPAND
- 白话认路
source:
  conversation: cb47efd7-68ce-4970-9af1-8ef2b26869b1
---
自检收口结论：normalize_for_route 只做短词替换、append_extras=False，避免「变成」带出「别画原来」污染规则。
句末紧贴表情/姿势才抑制换题材；同一身份优先变体。
软合成（升档那条）强制问；icon_unspecified/hard_ambiguity 抬 announce 为人话 ask。
仍开放（med）：「变成微笑的她再画」叠后缀、「改成她微笑」代词在前，可能误克隆。
