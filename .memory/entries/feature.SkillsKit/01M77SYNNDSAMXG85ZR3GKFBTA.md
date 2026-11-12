---
id: 01M77SYNNDSAMXG85ZR3GKFBTA
module: feature.SkillsKit
entity: StyleSourcePriority
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/delivery_gates.py#generate_prefix
- skills_kit/delivery_gates.py#_player_style_texts
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: merge默认锁点名风格认合同locks/vibe/原话
verify: unittest tests.test_final_prompt_gate.TestGeneratePrefixContractStyle -q
applies: merge 会话已 contract set 风格锁但 goal 未点名时
source:
  conversation: b184581b-9d2c-4d9d-9f09-b09811f9f431
---
需求来源：goal 漏写风格但合同已锁水彩等时，generate_prefix 仍钉 GH 默认盖过本意。
必须保持：delivery_gates._player_style_texts 聚合 goal+L1 locks+commercial_vibe+raw_utterance；
player_named_style 命中则不注入 merge 默认 surface；
完整硬句跳过仍只看 prompt（不含把 Warm-Start 赛博当点名的回潮）。
适用：merge converge generate_prefix。
入口：skills_kit/delivery_gates.py generate_prefix。
