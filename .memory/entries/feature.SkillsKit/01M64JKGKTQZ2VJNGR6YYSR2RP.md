---
id: 01M64JKGKTQZ2VJNGR6YYSR2RP
module: feature.SkillsKit
entity: AgentRoute
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/colloquial_lexicon.py
- skills_kit/data/colloquial_expand.jsonl
- skills_kit/data/artist_talk_100.jsonl
- tests/test_artist_talk_accuracy.py
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 口语扩展表≥8000条接入认路折叠与100句白话准确率门禁
verify: unittest tests.test_artist_talk_accuracy 100/100；colloquial_expand.jsonl≥8000
applies: /pmem-agent 与 pmem_art.py route 白话认路
source:
  conversation: cb47efd7-68ce-4970-9af1-8ef2b26869b1
---
需求：深度扩展口语形似表（建议8000）、跑路由测修好、再以约100句美术白话做匹配比对，准确率要非常高。
必须保持：检索仍是字面n-gram+扩展；plan_route 认路前短口语表面折叠；长键不吞题材；糊话强制问；2525规则回归不被向量语义替换。
入口：skills_kit/colloquial_lexicon.py 生成/加载；
route_normalize.normalize_for_route / expand_colloquial；
advise_route→plan_route；
门禁 tests.test_artist_talk_accuracy。
适用：玩家大白话进 /pmem-agent / route。
