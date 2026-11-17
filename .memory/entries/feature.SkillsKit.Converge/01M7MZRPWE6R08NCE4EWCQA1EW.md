---
id: 01M7MZRPWE6R08NCE4EWCQA1EW
module: feature.SkillsKit.Converge
entity: SkillRoundCap3
kind: feature
status: active
supersedes:
- 01M6YDZ9G75M6GPQC90QG6DRXB
anchors:
- skills_kit/prompt_scale.py#DEFAULT_MAX_ROUNDS
- skills_kit/converge.py
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 生图闭环默认最多3轮·到线即停
verify: 'rg "max_rounds: 3" .memory-art/config.yaml；DEFAULT_MAX_ROUNDS==3；unittest
  tests.test_skill_speed_caps -q'
applies: 日常 converge quality 出图
aliases:
- 三轮上限
- max_rounds 3
source:
  conversation: dd2cd25b-2389-481d-b74f-49e53cac04fb
---
需求来源：玩家要求全部改成最多三轮，四轮太耗时。
必须保持：≥9.5 到线即停；
硬顶 max_rounds=3（DEFAULT_MAX_ROUNDS 与各技能 cap 常量一致）；
满3轮交历史最高分并标明是否过线；
关系讨论仍最多2稿；
本项目可叠加 safe_early_stop 提前交最高分。
适用条件：日常 quality 交付（普通图/原画/克隆/变体/多图/UI/Icon关键枚/merge整表与逐格）。
入口：converge start 读 config.max_rounds 或 CLI --max-rounds；技能文案【最多3轮·到线即停】。
