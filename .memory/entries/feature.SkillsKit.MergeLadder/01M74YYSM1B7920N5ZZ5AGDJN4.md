---
id: 01M74YYSM1B7920N5ZZ5AGDJN4
module: feature.SkillsKit.MergeLadder
entity: FreshRelationDefault
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- .cursor/skills/pmem-merge-ladder/SKILL.md
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 合成梯未点名接续必须新开关系稿与目录
verify: grep 未点名接续 skills_kit/skill_specs.py .cursor/skills/pmem-merge-ladder/SKILL.md
applies: 合成梯新开任务、玩家未点名旧稿时
aliases:
- 新开关系稿
- 禁止复用旧 merge yaml
source:
  conversation: 7f6eb6c5-c94f-491f-9845-6667f9d3d230
---
需求来源：玩家要求通用解法，避免执行侧未授权复用仓库旧水果关系稿导致风格与档序被旧轨锁死。
必须保持：未点名「接着上次/用这份稿/旧目录」时，合成梯新写 phase1、并列新输出目录、新 session；
只可借 yaml 字段格式，不可借旧题材档序与旧成图像素身份；
首轮若偏写实/产品静物，下一轮整张重开并强调糖釉玩具硬句，禁止只垫上轮硬3D微修。
适用条件：/pmem-merge-ladder 或路由判成 merge.ladder，且玩家未点名接续。
入口：技能执行卡第2步与开场「先认接续」；禁止条「未点名却复用」。
