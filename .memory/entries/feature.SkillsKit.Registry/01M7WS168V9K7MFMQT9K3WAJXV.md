---
id: 01M7WS168V9K7MFMQT9K3WAJXV
module: feature.SkillsKit.Registry
entity: LayerSplitPack
kind: conclusion
status: seed
supersedes: []
anchors:
- skills_kit/skill_registry.py
- skills_kit/data/pmem_layer_split_skill_body.md
- tests/test_skill_router.py
- tests/test_showcase_gate.py
- skills_kit/showcase_gate.py
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: layer.split执行包只装执行卡+交件，禁止整份H1
verify: python -c "from skills_kit.skills_verify import verify_skills; assert verify_skills(quick=True)['ok']"；pytest
  tests/test_skill_router.py::SkillRouterTests::test_primary_contracts tests/test_showcase_gate.py
  tests/test_skill_hardening.py::SkillsVerifyTests::test_verify_quick -q
applies: 改 pmem-layer-split 正文或 layer.split pack_headings / 技能清单时
trust:
  status: candidate
  verification: unverified
version: 1
content_sha256: 84ffcc3755940a17dcfa87413b77239837c276d0c6ebff7e08e09b73b13b6f23
space:
  profile_id: project
  owner_id: ''
  project_id: Cursor-Pmem-Art
  module_id: feature.SkillsKit.Registry
  entity_id: LayerSplitPack
provenance:
  source_type: conversation
  source_id: ''
  extracted_by: ''
  recorded_by: 1002378395@qq.com
layer: memory
profile_id: project
profile_kind: conclusion
---
现象：skills --verify 报 layer.split:285>120；PRIMARY 测试仍写十技能不含 pmem-layer-split。
原因：registry 把 H1 整份合同塞进 pack_headings；测试清单未跟 SKILL_SPECS。
修法：技能正文加「执行卡 · 拆图层」；pack 改为执行卡+交件可见；PRIMARY 列入 pmem-layer-split；skills --install 同步三端 SKILL.md。
showcase_gate/DEFAULT_MAX_ROUNDS=3：未满3轮未过线才拦，测试从按4轮口径改按3轮。
