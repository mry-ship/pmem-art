---
id: 01M7PPZ0QT7T5JDWNVGRPS23ZG
module: feature.SkillsKit
entity: DeliveryVisibleElapsed
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/process_board.py#stamp_elapsed
- skills_kit/process_board.py#write_process_sheet
- skills_kit/process_board.py#format_rounds_click_table
- skills_kit/converge.py
- skills_kit/skill_registry.py#_draw_pack_headings
- skills_kit/skill_specs.py
revision: git:fdcc718
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 出图结算必须贴拼板和可点轮次表，末行写本次耗时
verify: py -3 -m unittest tests.test_process_board tests.test_skill_router -q
applies: 跑过 converge finish 的出图：普通图/原画/克隆/变体/多图/UI/图标/合成梯。镜头包点选前、提示词、审图、归档、教练不套。
aliases:
- 轮次表
- 过程拼板
- 本次耗时
- 可点图
verified: '2026-11-20'
verified_at: '2026-11-20T17:02:25.781+08:00'
---
需求来源：玩家要求技能结算都有可点开的轮次表、过程拼板（分数/不足），并在最后显示本次耗时。之前有的技能不会这么交。
必须保持：
1) 出图 route 的执行包含「## 交件可见」：Read process_sheet.jpg、贴轮次单图表（轮次×分数×可点图）、再 Read 每一轮原图、结算末行写本次耗时。
   覆盖 draw.普通图/克隆/变体/多图/原画、ui.kit、merge.ladder、icon.a/b/c。
2) converge finish 用会话 started_at 到结算时刻写 elapsed_text，打进报告末行、过程拼板页脚、轮次表。没有 started_at 则不编造耗时。
3) 镜头包点选前不生图、提示词、审图、归档、教练的执行包不带这一节。
入口：stamp_elapsed / write_process_artifacts / converge finish；skill_registry 的 pack_headings。
