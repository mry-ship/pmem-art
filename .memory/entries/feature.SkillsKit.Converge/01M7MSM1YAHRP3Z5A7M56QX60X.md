---
id: 01M7MSM1YAHRP3Z5A7M56QX60X
module: feature.SkillsKit.Converge
entity: ProcessSheetPrimary
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/process_board.py#format_rounds_click_table
- skills_kit/process_board.py#write_rounds_table
- skills_kit/converge.py
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: finish 双主交件：过程图拼板 + 轮次单图表（可点开）；HTML 旁路
verify: unittest tests.test_process_board -q；boards/*/rounds.md 含「轮次单图表」
applies: 日常 converge finish 交件与 Agent 结算展示
aliases:
- 轮次单图表
- rounds.md
- 可点图表格
---
需求来源：玩家明确要「拼板 + 几轮×每轮单独可点图」两样都有，不能只交拼板。
必须保持：
1) process_sheet.jpg 过程图拼板（总览分数/不足/胜出框）；
2) rounds.md + finish 报告内 Markdown 表（轮次|分数|可点图链接），链接指向 boards/.../images/rN；
3) Agent 结算：Read 拼板 + 贴单图表 + Read 每一轮原图；禁止只交拼板或只甩 HTML；
4) sess 写 process_sheet / process_rounds / process_board。
入口：format_rounds_click_table / write_rounds_table / write_process_artifacts；converge finish。
