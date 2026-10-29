---
id: 01M642X6FRM31CR13JD8RQZQZN
module: feature.Improve
entity: AutoAccept
kind: exclusion
status: seed
supersedes: []
anchors:
- improve/knowledge.py#cmd_learn
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 禁止自动accept全部知识卡，教练收下必须用户点名
verify: pmem-coach 规格含禁止自动 accept --all
aliases:
- accept-all
- 知识卡
---
依据 test_skill_router 与 pmem-coach 规格：禁止自动 learn/coach accept --all。
finish 后的静默 autopilot 可以排队建议，但不能替用户收下知识卡。
排除：为了「记忆库丰满」在 Agent 里直接 accept --all。
