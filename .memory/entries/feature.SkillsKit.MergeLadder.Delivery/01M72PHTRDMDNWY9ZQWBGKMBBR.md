---
id: 01M72PHTRDMDNWY9ZQWBGKMBBR
module: feature.SkillsKit.MergeLadder.Delivery
entity: OverviewPromptAndCard
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#_cell_fragment_rows
- .cursor/skills/pmem-merge-ladder/SKILL.md
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 浅色卡+出图模板仍有效；拼贴须靠残片硬闸，不能只靠文字清单
verify: audit_overview_sheet 对拼贴终稿返回贴边残片硬伤；技能仍含浅色圆角卡与出图提示词模板
applies: merge overview_sheet
aliases:
- 拼贴清单虚标
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
先前功能记录把「审图查拼贴残片切顶」写成已交付，但当时只有 SKILL 禁令与验收清单，audit 不管拼贴，jam/wind 拼贴终稿仍 ok=True。
现必须保持：文字清单仍在；
真正拦拼贴靠 _cell_fragment_rows 硬伤（见 FragmentCollageGate）。
浅色圆角卡与出图提示词模板不变。
多游戏真链档序见 docs/MERGE_CHAIN_REFERENCE.md。
