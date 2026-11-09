---
id: 01M6P44HS52M1ZEE1EVY1JEZRR
module: feature.SkillsKit.StyleLock
entity: StyleLockDeliveryContract
kind: feature
status: active
supersedes:
- 01M6P1XAG967EG48WEFNQHSSN2
anchors:
- skills_kit/skill_specs.py
- feedback.py#cmd_feedback
- .agents/skills/pmem-style-lock/SKILL.md
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: style-lock 显式选模块，写入风格决策、每张样图配方与红线
verify: 检查 skills_kit/skill_specs.py 与三端 SKILL.md/command 正文一致；确认每条命令带同一 --module、每张样图一条
  --kind recipe；feedback.py 显示 recipe 以 approved 角色写入。
applies: 用户提供 1–3 张满意样张并要求锁定项目或角色风格时。
source:
  conversation: 01a1abb8-0adc-7403-bf8c-04a43e507842
---
需求来源：修复技能合同与实际记忆写入路径不一致的问题。
必须保持：每条写入显式指定同一目标模块；
玩家点名模块则使用该模块；
指定单角色且无现有模块时用 character.<slug>；
其他未指定范围时用项目级 brand.WorldStyle。
把每张玩家提交的满意样张各写一条关联资产的 recipe（approved 正向锚点），并写 art_decision 与 style_redline；
卡片列出三类实际记录路径。
入口：/pmem-style-lock 及其三端 slash-command。
省略 --module 会进入 _inbox/pending，因此禁止省略。
