---
id: 01M70S95SPAVPCKNWJCZ562HEM
module: feature.SkillsKit.Agent
entity: DriftResetRule
kind: feature
status: active
supersedes:
- 01M6GN5JCVC4X390H9TE8A2QM3
anchors:
- skills_kit/install.py#_render_agent_doc_block
- .cursor/rules/pmem-art.mdc
- tests/test_skill_router.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 跑偏纠偏口语触发词补「不符合」等否词，并与 L0 合同词表对齐
verify: python3 -m unittest tests.test_understanding_contract.TestUnderstandingContract.test_classify_layers
  -q；rg 不符合预期 .cursor/rules/pmem-art.mdc skills_kit/understanding_contract.py
applies: pmem-art init 或 install_skills 写入总规则后；contract classify 画师反馈时
aliases:
- drift_reset
- 跑偏重置
---
需求来源：画师常说「不符合/对不上/不是我想要的」，旧词表偏「不对」易漏触发，多轮仍沿用错理解。
必须保持：skills_kit/install.py 的 _render_agent_doc_block「### 5. 跑偏纠偏」否定翻车含 不符合/不符合预期/不符合要求/对不上/差太远/不是我想要的/不是我要的/没按我说的/跟我说的不一样/画错了/做错了/不是这个意思/不是这个效果/翻车了；
要求重开含 上一套作废/全部作废；
要求换路含 别按旧的做/不要按旧方案。
必须保持：understanding_contract._L0_PATTERNS 与上列同向（含 答非所问、不符合 等）；classify「不符合预期」等为 l0。
仍排除局部微调不当跑偏；仍是规则+合同归层，非物理清空聊天上下文。
init/install 同步写入 .cursor/rules/pmem-art.mdc、CLAUDE.md、AGENTS.md。
