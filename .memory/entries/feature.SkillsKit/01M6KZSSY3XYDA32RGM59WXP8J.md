---
id: 01M6KZSSY3XYDA32RGM59WXP8J
module: feature.SkillsKit
entity: CommercialBenchmarkDiagnose
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/install.py#_render_agent_doc_block
- skills_kit/skill_specs.py
- tests/test_skill_router.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 终稿拿不准时商业对标诊断准则
verify: rg 终稿商业对标诊断 .cursor/rules/pmem-art.mdc；python -m unittest tests.test_skill_router.SkillRouterTests.test_install_keeps_one_command_per_skill
applies: pmem-art init 或 install_skills 写入总规则后；出图终稿拿不准或 /pmem-critique 审图时
---
需求来源：画师要求 skill 出图终稿拿不准时，找同品类顶级商业范例对比，定性理解/合理性/完成度等问题。
必须保持：skills_kit/install.py 的 _render_agent_doc_block 含「### 6. 终稿商业对标诊断」；写明同品类顶级商业范例并排对比、问题类型定性、禁止当垫图抄构图/抄机位、结算写清对标与诊断。
必须保持：pmem-draw Step 3 有「终稿拿不准时（商业对标诊断）」钩子；pmem-critique 有「拿不准时先商业对标」步骤。
init/install 同步写入 .cursor/rules/pmem-art.mdc、CLAUDE.md、AGENTS.md 与技能副本；只改本地 mdc 会被覆盖。
仍是规则约束非硬编码扫描。
