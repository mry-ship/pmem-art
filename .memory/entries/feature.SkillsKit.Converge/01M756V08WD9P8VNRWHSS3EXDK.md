---
id: 01M756V08WD9P8VNRWHSS3EXDK
module: feature.SkillsKit.Converge
entity: AutoRecall
kind: correction
status: active
supersedes:
- 01M643RQVC741VT5CB5NSFBHQG
anchors:
- skills_kit/converge.py
- skills_kit/skill_specs.py
- skills_kit/install.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 并入只认 generate；默认不再 Hook 二灌
verify: unittest tests.test_auto_recall.TestSkillSpecForbidsHandPaste tests.test_auto_recall.TestGenerateMergesMemory
  -q；rg "再用 `updated_input` 灌一次" skills_kit/skill_specs.py 无命中
applies: 跑 /pmem-draw 等生图技能或 converge generate 时
aliases:
- Warm-Start 并入
- search 可选项
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧功能仍写 GenerateImage pre-gen 用 updated_input 再灌 Warm-Start。
现状：pre-gen 默认不挂且默认不灌；并入只认 converge generate 的 prompt_block / WARM_START_MERGED。
search --module 只给人看召回，不是并入本身。
技能与规则文案已改为禁止用「Hook 有没有跑」判断是否并入；仅 PMEM_ART_PRE_GEN_INJECT=1 调试才允许 Hook 灌入。
