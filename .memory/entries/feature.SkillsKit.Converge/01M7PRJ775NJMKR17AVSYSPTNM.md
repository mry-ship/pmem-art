---
id: 01M7PRJ775NJMKR17AVSYSPTNM
module: feature.SkillsKit.Converge
entity: FinalSlotInAssets
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_finish_write_final_slot
- skills_kit/converge.py#_apply_finish_memory_and_atlas
revision: git:fdcc718
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 终稿槽只写项目 assets 里的 final，工作台才能看见定稿
verify: py -3 -m unittest tests.test_process_board.ProcessBoardTests.test_final_slot_stays_inside_assets
  -q
applies: converge finish 把胜出图交给工作台主画廊时
aliases:
- 不进工作台
- 画廊看不到
- final.jpg
source:
  conversation: 4bd64c18-9a6e-4b02-afea-1f7610ef98f1
---
现象：生成图结算后工作台主画廊没有这张定稿。
原因：finish 时胜出图还在 Cursor 生成目录（仓库外），终稿槽写成了那里的 final.jpg。工作台只扫项目 assets/。后来拷进 assets 的文件名带 rN，主画廊按过程图藏起来。
必须保持：终稿槽只写项目内 assets/.../final.*；图还在仓库外时不写。settle 把胜出图拷进 assets 之后、刷新工作台之前，再写一次终稿槽。rN 仍留在进化对照，不进主画廊。
入口：_finish_write_final_slot；_apply_finish_memory_and_atlas 在拷贝后调用它。
