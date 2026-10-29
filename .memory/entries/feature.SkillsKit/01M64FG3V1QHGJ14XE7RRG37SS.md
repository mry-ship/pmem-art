---
id: 01M64FG3V1QHGJ14XE7RRG37SS
module: feature.SkillsKit
entity: AgentRoute
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/route_ask.py
- skills_kit/route_gate.py
- skills_kit/route_bank.py#advise_route
- USER_MANUAL.md
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 零门槛：糊话强制问、route闸门、对人只贴artist_say
verify: python3 pmem_art.py route --text "那个图标弄下" --brief 含先问你；画一张窗边女孩可 execute_ok；无
  last_advise 时 converge start 非零
applies: /pmem-agent 大白话与 converge 开画
aliases:
- 本地路由
- route_bank
- 话术库
source:
  conversation: cb47efd7-68ce-4970-9af1-8ef2b26869b1
---
需求来源：美术零门槛，不能默默走错普通图，也不能让画师碰 CLI。
必须保持：advise_route 对图标未分档/合成继续/无图指代/锁风格无样张等糊话返回 confidence=ask 并 stop；
对美术只展示 artist_say；
route 成功写入 last_advise；
converge start 默认校验路由闸门（--skip-route-gate 或环境 PMEM_ART_SKIP_ROUTE_GATE 可跳过）；
手册开篇改为直接说人话并链 route_pipeline.html。
入口：route_ask.detect_vague_ask；route_gate；route --brief；converge start。
