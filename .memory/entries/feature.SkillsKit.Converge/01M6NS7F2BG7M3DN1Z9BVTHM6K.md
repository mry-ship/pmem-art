---
id: 01M6NS7F2BG7M3DN1Z9BVTHM6K
module: feature.SkillsKit.Converge
entity: MergeLadder
kind: correction
status: active
supersedes:
- 01M6JW8CH2W2HYZ5SB062D3ZV5
anchors:
- skills_kit/skill_specs.py
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 关系稿上限改为最多2（可早停）
verify: AGENTS.md / skill_specs 含「最多 2 稿」；discuss 第3稿 exit 1
applies: /pmem-merge-ladder overview_sheet 关系段
---
旧结论「合成梯关系固定 3 稿」已不成立：overview_sheet 现为最多 2 稿（CLI discuss 第 3 稿拒写），第 1 稿过五问+relation-judge+商业对标+画风一句即可早停出图。
合同其它锁句（说不通不算、画风一句、同框非交货等）仍有效；
「每一档单独正方形」仅 per_cell，默认整表一组。
