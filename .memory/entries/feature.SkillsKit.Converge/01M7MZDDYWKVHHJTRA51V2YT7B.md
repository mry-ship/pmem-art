---
id: 01M7MZDDYWKVHHJTRA51V2YT7B
module: feature.SkillsKit.Converge
entity: EarlyStopIgnoresGateNotes
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: judge早停不再要求本轮无gate_notes
verify: tests.test_converge_guards.TestPolicyDefaults.test_early_stop_block_ignores_gate_notes_guard
applies: converge judge 且会话已开安全早停
verified: '2026-11-17'
verified_at: '2026-11-17T22:46:45.693+08:00'
source:
  conversation: e0bcd255-9b2c-44ae-9421-7ea0137157aa
---
需求来源：不伤质量加速出图墙钟（狗狗 merge 白跑 R3/R4）。
必须保持：≥9.5 到线即停；早停只交历史最高分；不降门槛。
行为：converge judge 在 safe_early_stop 开启时，即使本轮有 gate_notes（如 merge 贴边残片），仍可触发 STOP_PLATEAU/STOP_REGRESSION 并 ready_to_finish。
适用：项目 config safe_early_stop=true（本仓已开，plateau_rounds=1）。
入口：skills_kit/converge.py judge 分支；会话 start 写入 plateau_rounds。
