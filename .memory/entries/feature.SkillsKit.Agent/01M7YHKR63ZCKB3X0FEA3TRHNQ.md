---
id: 01M7YHKR63ZCKB3X0FEA3TRHNQ
module: feature.SkillsKit.Agent
entity: UnderstandingContract
kind: correction
status: active
supersedes:
- 01M70BK8V2GG819Y1Z6NJ9G982
anchors:
- skills_kit/understanding_contract.py#apply_feedback
revision: git:0b7e1e8
author: yanghu
note_date: '2026-11-21'
summary: 理解合同硬顶是最多3轮，L1不自动填四格
verify: python3 -m unittest tests.test_understanding_contract.TestUnderstandingContract.test_l1_patch_short_lock_not_full_sentence
  tests.test_understanding_contract.TestUnderstandingContract.test_bootstrap_leaves_grid_unwritten
  -q
applies: 读理解合同注释、L1 反馈或 converge 轮次硬顶时
---
旧结论把理解合同的必须保持写成最多4轮。该句已过时。现行生图硬顶是最多3轮、合格线仍是9.5。
仍成立的部分：understanding_contract 外置当前理解；converge start 写入合同；loop_followup 附工作集；CLI contract；不改 route 闸、垫图和续写硬约束。
更正：模块注释与 converge 注释已改成最多3轮。
contract_from_session_bootstrap 仍不填四格。
L1 反馈只写入 l1.locks，不再把「保持机位」抄进 grid.keep。
四格为空时 generate 会标明本轮不受四格约束。
