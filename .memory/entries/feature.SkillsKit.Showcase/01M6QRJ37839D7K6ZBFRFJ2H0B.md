---
id: 01M6QRJ37839D7K6ZBFRFJ2H0B
module: feature.SkillsKit.Showcase
entity: ShowcaseBareIconDrop
kind: correction
status: active
supersedes:
- 01M6QR8DE3Y96BJ3ME26X7EBJY
anchors:
- skills_kit/agent_router.py#_showcase_bare_icon
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 已修：展陈裸图标停问不再丢支执行
verify: plan_route('对比页把图标和合成梯都再跑一遍').reason=='icon_unspecified'
applies: 改 agent_router._showcase_ids 或默认兜底时
---
旧风险：裸图标被丢只剩 merge 且执行。现 _showcase_bare_icon 触发 icon_unspecified；并补图标A/B/C 探针。
