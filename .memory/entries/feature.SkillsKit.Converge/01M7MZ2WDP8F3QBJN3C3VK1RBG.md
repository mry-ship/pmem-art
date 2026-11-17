---
id: 01M7MZ2WDP8F3QBJN3C3VK1RBG
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: correction
status: active
supersedes:
- 01M736ZGH8S10JHTT8KA24FQM4
anchors:
- .memory-art/config.yaml
- skills_kit/converge.py#cmd_converge
- skills_kit/converge_policy.py#decide_round_stop
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 本项目已开safe_early_stop；库默认仍关
verify: 'rg "safe_early_stop: true" .memory-art/config.yaml；DEFAULT_SAFE_EARLY_STOP
  is False'
applies: 本仓库日常 converge quality 交付
aliases:
- 安全早停已开
- plateau_rounds
verified: '2026-11-17'
verified_at: '2026-11-17T22:41:16.807+08:00'
source:
  conversation: dd2cd25b-2389-481d-b74f-49e53cac04fb
---
旧结论：本仓库 converge.safe_early_stop 与项目 config 均为关，未写成 true 时掉分/平台不能在第4轮前停。
更正：自本决策起，工作面 `.memory-art/config.yaml` 与 `.memory-art/projects/pmem-art/config.yaml` 均为 safe_early_stop=true、plateau_rounds=1、regression_drop=0.15、early_stop_min_round=2。
库内 DEFAULT_SAFE_EARLY_STOP 仍为 false（未写配置的仓库/测试不变）。
judge 读 sess.plateau_rounds。
到线仍≥9.5；
早停只交历史最高分。
