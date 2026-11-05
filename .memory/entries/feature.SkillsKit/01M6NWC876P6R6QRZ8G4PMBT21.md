---
id: 01M6NWC876P6R6QRZ8G4PMBT21
module: feature.SkillsKit
entity: SkillNavIndexGuard
kind: correction
status: active
supersedes:
- 01M6NR18YRG1910EZAH15HQTJ9
anchors:
- skills_kit/skill_registry.py#_draw_pack_headings
- skills_kit/skill_registry.py#_mode_heading
- skills_kit/skill_registry.py#_parse_draw_table
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 导航表只做目录，不能改切片和路由解析
verify: slice_route_body 对 draw.clone 仍含零点五与合同；icon.a 的 heading 仍是 Mode A 正文节
applies: 改 skill_specs 里的技能导航、标题或表头时
aliases:
- 导航表
- pack_headings
- 技能索引
---
对照 skills_kit/skill_registry.py 的 _draw_pack_headings 与 _icon_routes：draw 的普通图、克隆、变体、多图分工、原画执行包已含「## 零点五」与「## 二、」，除镜头包外再加对应合同，并含记忆静默；
icon 执行包已含 Mode 节、### Mode 清单与记忆静默。
旧更正里「ordinary 切片不含零点五」「合同裁节不带公共闭环」与当前代码不符。
仍成立的部分：icon Mode A/B/C 是并列的独立二级标题；双参考同框仍是能力缺口并硬停。
给技能加导航时只做目录。
禁止新增一级标题，否则从技能开头 H1 裁切的执行包会在新 H1 处截断。
draw 的新表表头不要用「| 认成」，否则 _parse_draw_table 会把它当成路由行。
icon 的新标题行不要包含 Mode A、Mode B、Mode C，否则 _mode_heading 会把导航当成模式节。
格子只写现有标题名，停止条件、评分门槛和禁区留在原段落。
