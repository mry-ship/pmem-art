---
id: 01M6P1ZBSV2MXR1F2FDF1N9F1G
module: feature.SkillsKit.Atlas
entity: AtlasApprovalBoundary
kind: risk
status: active
supersedes: []
anchors:
- AGENTS.md
- .agents/skills/pmem-atlas/SKILL.md
- skills_kit/skill_specs.py
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: pmem-atlas 总说明称自动归档，技能正文要求移动前同意
verify: 对照 AGENTS.md 的 /pmem-atlas 描述与 .agents/skills/pmem-atlas/SKILL.md 中 classify-watch、--apply
  的规则；修订后再检查三端安装副本一致。
applies: 执行 /pmem-atlas 且 classify-watch 找到可归档文件时。
source:
  conversation: 01a1abb8-0adc-7403-bf8c-04a43e507842
---
项目总说明和 pmem-atlas description 将能力写作自动扫描并归位/归档；
技能执行步骤则要求先报告待归档文件，只有用户同意后才传 --apply 移动。
两处对是否可自动移动的授权边界不一致，可能让 Agent 在同一请求中表现不一。
需要统一文案与行为；
现阶段按技能正文的显式确认要求执行。
