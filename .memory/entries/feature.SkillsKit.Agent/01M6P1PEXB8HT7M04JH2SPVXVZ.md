---
id: 01M6P1PEXB8HT7M04JH2SPVXVZ
module: feature.SkillsKit.Agent
entity: SkillSuiteNaming
kind: decision
status: active
supersedes: []
anchors: []
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 侧栏与目录直接叫技能
---
需求来源：玩家说「直接叫技能不就好了」，不要电池/技能测/suite。
必须保持：Task description 用「技能·普通图/原画/…」；
目录 assets/skill_YYYYMMDD/；
禁止电池、battery、技能测、skill_suite、skill_battery。
适用：/pmem-agent 并发子 agent、技能全检。
入口：.cursor/skills/pmem-agent/SKILL.md。
