---
id: 01M6NXC1SJ2RJAMZSZTHYW9C4S
module: feature.SkillsKit.Registry
entity: SkillNavCompleteness
kind: correction
status: active
supersedes:
- 01M6NX80FSC08AQSA623V0NWEK
anchors:
- skills_kit/skill_registry.py#_draw_pack_headings
- skills_kit/skill_registry.py#_icon_routes
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 导航只留章节名，执行包恢复原裁剪
verify: ordinary 包不含支持两种触发方式；icon.a 的 pack_headings 不含耗时闸；icon 正文无三档对照；section_cut_ok
applies: 改 draw、icon、merge、agent 的目录或执行包裁剪时
aliases:
- 章节导航
- 子合同目录
---
复查后收回会改执行结果的增补。普通图和原画的执行包不再加入「一、支持两种触发方式」。图标执行包不再加入耗时闸，恢复为 Mode 节、同档清单和记忆静默。
图标正文去掉「三档对照」，避免和注册表的 A/B/C 分路、模式节、第五节清单并列成第二份表。
认成表第三列恢复原句。draw 只留「子合同目录」，merge 和 agent 只留「章节导航」，格子里只有章节名。门槛、禁区和路由规则仍以原节为准。
