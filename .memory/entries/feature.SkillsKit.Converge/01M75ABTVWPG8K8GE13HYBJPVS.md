---
id: 01M75ABTVWPG8K8GE13HYBJPVS
module: feature.SkillsKit.Converge
entity: AutoRecall
kind: correction
status: active
supersedes:
- 01M756V08WD9P8VNRWHSS3EXDK
anchors:
- skills_kit/skill_specs.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 出图必须用 generate 最终 Prompt；无 Hook 灌词
verify: unittest tests.test_auto_recall.TestSkillSpecForbidsHandPaste -q；技能正文含「最终
  Prompt（出图须用这句）」
applies: 跑 /pmem-draw 等生图技能或 converge generate 后出图时
aliases:
- 必须用最终 Prompt
verified: '2026-11-11'
verified_at: '2026-11-11T21:41:56.506+08:00'
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧 AutoRecall 仍写可 PMEM_ART_PRE_GEN_INJECT=1 调试灌入。
更正：Hook 永不灌；
Agent 调 GenerateImage/外部生图必须用 converge generate 打印的「最终 Prompt（出图须用这句）」；
禁止另写 brief、禁止手贴 Warm-Start。
search 仍只给人看。
