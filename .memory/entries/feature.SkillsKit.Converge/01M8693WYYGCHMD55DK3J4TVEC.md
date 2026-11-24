---
id: 01M8693WYYGCHMD55DK3J4TVEC
module: feature.SkillsKit.Converge
entity: RegisterSkipsRecompose
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#reuse_pending
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 登记成图复用已定稿，不再重算提示词
verify: pyw -3 -u -m unittest tests.test_converge_emit_prompt -q
applies: converge generate --image 登记本轮已 emit 的最终 Prompt 时
aliases:
- 缩短一半
source:
  kind: conversation
---
所有技能登记成图时，如果这轮最终 Prompt 已经由 emit 定稿，就直接挂上图片。
不再重跑合理性、Warm-Start 和提示词装配，也不再把整段提示词和审图长文打出来。
画面和分数仍用那份定稿。
合格线仍是 9.5。
生图接口一次一张，该画的轮次不能并进同一次调用。
