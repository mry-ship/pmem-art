---
id: 01M643RQVC741VT5CB5NSFBHQG
module: feature.SkillsKit
entity: AutoRecall
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
- skills_kit/skill_specs.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 生图技能必须自动并入Warm-Start，search只是给人看的可选项
verify: python -m unittest tests.test_auto_recall.TestGenerateMergesMemory tests.test_auto_recall.TestSkillSpecForbidsHandPaste
  -v
applies: 跑 /pmem-draw 等生图技能或 converge generate 时
aliases:
- 自动召回
- 已自动并入记忆
---
需求来源：用户发现跑 skill 时对话里看不到记忆，要求修复自动查看记忆。
必须保持：converge generate 默认 apply_memory 时把 sess.warm_start.prompt_block 并入提示词，对话回显「pmem-art 已自动并入记忆」；
同一 prompt_block 已在文中则不再重复灌。
GenerateImage 的 pre-gen Hook 用 updated_input 再灌一次，Write/Edit 不改文件内容。
search --module 只是给画师看召回结果的可选项，不是召回本身。
入口：python pmem_art.py converge generate；python pmem_art.py hook pre-gen；/pmem-draw 技能正文。
