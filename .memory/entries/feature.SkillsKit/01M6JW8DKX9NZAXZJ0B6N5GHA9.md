---
id: 01M6JW8DKX9NZAXZJ0B6N5GHA9
module: feature.SkillsKit
entity: ReasonablenessGate
kind: conclusion
status: active
supersedes: []
anchors:
- tests/test_auto_recall.py
- skills_kit/reasonableness_gate.py
revision: git:7f67ea9
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 测 Warm-Start 并入须先过合理性闸
verify: python -m pytest tests/test_auto_recall.py::TestGenerateMergesMemory::test_generate_prompt_contains_warm_start
  -q
applies: 写 converge generate 单测、测记忆并入而非闸门本身时
verified: '2026-11-06'
verified_at: '2026-11-06T20:55:59.451+08:00'
---
合理性闸门默认挡住首轮 generate。
测自动并入 Warm-Start 时，测试须先 review_reasonableness + apply_review_to_session（或显式 skip），不能假定 generate 直接放行。
误把闸门当回归失败会掩盖记忆并入路径。
