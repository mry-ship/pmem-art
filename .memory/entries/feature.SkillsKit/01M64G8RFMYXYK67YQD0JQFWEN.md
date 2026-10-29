---
id: 01M64G8RFMYXYK67YQD0JQFWEN
module: feature.SkillsKit
entity: AgentRoute
kind: decision
status: active
supersedes:
- 01M64FG7Z2EAC2CD5N4DEMYH29
anchors:
- skills_kit/route_normalize.py
- skills_kit/route_bank.py#advise_route
- docs/route_pipeline.html
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 路由匹配是字面n-gram；口语先标准句再route，不做向量语义
scope: project
verify: tests.test_route_advise 含 colloquial/canonical/conflict；打开 docs/route_pipeline.html
applies: /pmem-agent 未点名技能时的路由校准
aliases:
- 标准路由句
- 口语标准化
- 字面相似
source:
  conversation: cb47efd7-68ce-4970-9af1-8ef2b26869b1
---
取舍：检索保持字面 n-gram + 口语扩展表（COLLOQUIAL_EXPAND），不做 embedding 语义相似度。
美术口语先由 Agent 写成一行标准路由句（CANON_TEMPLATES），再 python3 pmem_art.py route --text 原话 --canonical 标准句。
规则 plan_route 仍以原话为准；标准句用于检索增强；仅 Agent 显式 canonical 与原话 route_ids 冲突时 plan_conflict 并降 confidence=low。
本地启发式 canonical 只助检索，不单独改判。
流程图：docs/route_pipeline.html（风险点已标红/琥珀）。
