---
id: 01M72SB0ED9YA2EYSBF75NXVAR
module: feature.SkillsKit
entity: AlphaBgPolicy
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py#_ALPHA_BG_POLICY
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: ALPHA_BG 顶栏注明合成梯整表浅色卡例外
verify: grep 浅色圆角卡 .cursor/skills/pmem-merge-ladder/SKILL.md
applies: 所有注入 ALPHA_BG_POLICY 的技能顶栏
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
需求：共用 _ALPHA_BG_POLICY 写「默认纯黑」会误导合成梯整表。
必须保持：第一条末尾写「例外：合成梯整表（overview_sheet）用浅色圆角卡，纯黑只给 per_cell」；对其它技能无害。改完须跑 install_skills_and_agent_configs 刷新各端 SKILL.md。
入口：skills_kit/skill_specs.py _ALPHA_BG_POLICY。
