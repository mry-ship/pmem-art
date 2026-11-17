---
id: 01M7MZ1NGAPQGJGW1CKNDMVBS1
module: feature.SkillsKit.Converge
entity: ProjectSafeEarlyStopOn
kind: decision
status: active
supersedes:
- 01M7MWP5T8FD683F43JG9N7N4E
anchors:
- .memory-art/projects/pmem-art/config.yaml
- skills_kit/converge.py
- skills_kit/converge_policy.py
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 本项目打开safe_early_stop+plateau_rounds=1省墙钟
verify: config safe_early_stop true + plateau_rounds 1；unittest tests.test_converge_guards
  OK；DEFAULT_SAFE_EARLY_STOP is False
applies: 本仓库 pmem-art 项目日常 quality 交付
aliases:
- 安全早停
- 墙钟加速
- plateau_rounds
verified: '2026-11-17'
verified_at: '2026-11-17T22:41:16.807+08:00'
source:
  conversation: dd2cd25b-2389-481d-b74f-49e53cac04fb
---
需求：在不影响质量（不降9.5到线、仍交历史最高分）的前提下加速日常出图墙钟。
决定：项目 config `.memory-art/projects/pmem-art/config.yaml` 设 converge.safe_early_stop=true、early_stop_min_round=2、regression_drop=0.15、plateau_rounds=1。
库默认 DEFAULT_SAFE_EARLY_STOP 仍为 false（测试与未写配置的仓库不变）。
plateau_rounds=1 对齐平台纪律「本轮≤历史最高→finish」，避免为凑满4再画掉分轮（如 RM 主界面 R3=8.65→R4=8.51）。
代码：converge start 写入 sess.plateau_rounds；
judge 的 decide_round_stop 改读会话而非写死 DEFAULT_PLATEAU_ROUNDS。
技能/AGENTS/规则文案改为「本项目已开」。
排除：不为省时间下调9.5门槛、不改回0.5/第4轮、不靠stub骗闸。
