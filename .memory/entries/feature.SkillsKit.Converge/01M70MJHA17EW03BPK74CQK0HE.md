---
id: 01M70MJHA17EW03BPK74CQK0HE
module: feature.SkillsKit.Converge
entity: ConvergeWinnerMaxScore
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
- pmem_art.py#_guess_final_image
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: finish 终稿必须取全场最高分
verify: 临时会话注入 R2=8.9 为最高，finish winner.round==2
applies: converge finish / 工作台进化对照
---
需求来源：玩家发现进化链终稿不是分数最高。
必须保持：未过线取全场最高分；
已过线取过线轮中最高分；
禁止先到线截断后轮、禁止结构闸剔掉更高分再定稿。
入口：skills_kit/converge.py finish；
pmem_art._guess_final_image 跟最高分轮。
