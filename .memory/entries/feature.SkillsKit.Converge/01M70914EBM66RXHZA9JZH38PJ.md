---
id: 01M70914EBM66RXHZA9JZH38PJ
module: feature.SkillsKit.Converge
entity: SkillStablePolish
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/must_fix.py#inject_must_fix
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: 稳定向打磨：MUST_FIX注入+暖启软门槛+Icon pack防串
verify: python3 -m unittest tests.test_must_fix tests.test_warm_start_guardrails -q；skills
  --verify
applies: 改 converge generate / warm-start / skill_registry section_cut 后
---
需求：在保证稳定性前提下继续技能优化（不改停机线/路由默认/不自动升 scale）。
必须保持：加法注入；vague goal 不误杀通用红线；Icon Mode 互不吞既有校验仍绿。
入口：skills_kit/must_fix.py（r2+ MUST_FIX≤2）；
improve/warm_start._soft_goal_overlap_ok（CJK bigram）；
skill_registry icon.a 禁 currentColor；
judge 仅提示可 --scale high。
