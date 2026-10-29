---
id: 01M642X5D4VXT06BTEPJWZCAFC
module: feature.Improve
entity: SharedKnowledge
kind: exclusion
status: seed
supersedes: []
anchors:
- improve/knowledge.py#is_style_agnostic_universal_card
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 项目专属色值和画风禁止上浮到跨项目共享知识层
verify: is_style_agnostic_universal_card 对带 HEX/角色词的卡返回 False
aliases:
- 共享知识
- 串风
---
依据 improve/knowledge.py：含项目专属 HEX、画风或角色词的知识卡禁止上浮到跨项目共享层。style_lock / 特定渲染技法卡只留项目私有层。排除：为了「复用」把本项目色板写进共享知识。
