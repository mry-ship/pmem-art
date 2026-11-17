---
id: 01M7MZ30EA04TK4BCQ6PDTBR3Q
module: feature.SkillsKit.Converge
entity: PlateauRoundsFromConfig
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py
- skills_kit/converge_policy.py#decide_round_stop
- .memory-art/config.yaml
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: plateau_rounds 可从 config 写入会话并参与早停
verify: 新会话 JSON 含 plateau_rounds；unittest tests.test_converge_guards OK
applies: converge start 之后的 judge 早停判断
source:
  conversation: dd2cd25b-2389-481d-b74f-49e53cac04fb
---
需求来源：质量不变墙钟加速——持平/掉分早停要对齐平台纪律。
必须保持：start 把 converge.plateau_rounds 写入会话；
judge 的 decide_round_stop 使用 sess.plateau_rounds（缺省仍 DEFAULT_PLATEAU_ROUNDS=2）；
本项目 config 写 1。
不改变 9.5 到线与交最高分语义。
入口：skills_kit/converge.py start/judge；config converge.plateau_rounds。
