---
id: 01M7YHKQRTHHNGRC7BQVWQSYBH
module: feature.SkillsKit.Converge
entity: UnderstandingContract
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
- skills_kit/understanding_contract.py#warm_needs_rebuild
revision: git:0b7e1e8
author: yanghu
note_date: '2026-11-21'
summary: 四格变更或清空都会重算暖启
verify: python3 -m unittest tests.test_understanding_contract.TestUnderstandingContract.test_bootstrap_leaves_grid_unwritten
  -q
applies: converge generate 且 apply_memory 时
---
需求来源：converge start 的合同只带目标和路由，四格要靠之后的 contract set。漏写时明确禁止不会挡历史记忆。四格一旦写入再清空，旧的 contract_stamp 会让 generate 继续用上一包。
必须保持：不在 bootstrap 自动填四格；route / 9.5 / 最多 3 轮 / 垫图硬闸不动。
落地：generate 在四格为空时打印「四格未写」。warm_needs_rebuild 在注入包缺失，或 stamp 与上次不同（含从有四格变回空）时重算，并把 contract_stamp 写成当前值。
入口：skills_kit/converge.py generate 路径；contract set 仍是写入四格的入口。
