---
id: 01M7MZD3JWNXMQ1CXYVJZWAV65
module: feature.SkillsKit.Converge
entity: EarlyStopIgnoresGateNotes
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
- skills_kit/converge_policy.py#decide_round_stop
- .memory-art/projects/cursor-pmem-art/config.yaml
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 早停不再被本轮gate_notes短路，仍交历史最高分
verify: unittest tests.test_converge_guards.TestPolicyDefaults -v 含 test_early_stop_block_ignores_gate_notes_guard
  与 plateau_rounds_1；rg "must NOT force burning" skills_kit/converge.py
applies: 本仓库 quality 交付且会话 safe_early_stop=true 时的 judge→finish
verified: '2026-11-17'
verified_at: '2026-11-17T22:46:45.693+08:00'
source:
  conversation: e0bcd255-9b2c-44ae-9421-7ea0137157aa
---
现象：狗狗 merge 整表虽项目已开 safe_early_stop，但 judge 里 `if not passed and should_continue and not gate_notes` 导致贴边残片等本轮 gate_notes 直接跳过 STOP_PLATEAU/REGRESSION，被迫凑满 4 轮（R2=8.56 后仍画 R3/R4）。
更正：去掉 `and not gate_notes`；早停交的是历史最高分，本轮审计提示仍可压本轮分，但不得逼烧剩余轮次。
配套：cursor-pmem-art/config.yaml 同步 safe_early_stop=true、plateau_rounds=1、max_rounds=4；merge 技能补墙钟三则（R1写准/早停/关系一稿过）。
不推翻：到线仍≥9.5；库 DEFAULT_SAFE_EARLY_STOP 仍 false。
