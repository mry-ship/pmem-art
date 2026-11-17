---
id: 01M7MZS6SJQ0FTPJG3QZKJCHK6
module: feature.SkillsKit.Converge
entity: SkillRoundCap3
kind: correction
status: active
supersedes:
- 01M6YDZBGSF7643HNT9YV83WR2
- 01M6YDZ9G75M6GPQC90QG6DRXB
anchors:
- skills_kit/prompt_scale.py#DEFAULT_MAX_ROUNDS
- skills_kit/converge.py#MERGE_OVERVIEW_MAX_ROUNDS
- .memory-art/config.yaml
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 生图闭环硬顶由最多4轮改为最多3轮
verify: assert DEFAULT_MAX_ROUNDS 与各 *_MAX_ROUNDS==3；unittest tests.test_skill_speed_caps
  tests.test_skill_router -q
applies: 所有 converge quality 出图路径的轮次硬顶
aliases:
- 最多3轮
- max_rounds=3
- 三轮兜底
source:
  conversation: dd2cd25b-2389-481d-b74f-49e53cac04fb
---
旧结论：普通图/UI/Icon/merge/多图等 converge ≥9.5到线即停、最多4轮兜底（SkillSpeedCaps / SkillRoundCap4）。
更正：墙钟过长，硬顶统一改为最多3轮；
DEFAULT_MAX_ROUNDS 与 MERGE_/UI_/ICON_/SPLIT_*_MAX_ROUNDS、项目 config max_rounds 均为3；
技能/AGENTS/规则/手册/registry 文案同步。
不推翻：到线仍≥9.5；关系稿上限仍2；本项目 safe_early_stop+plateau_rounds=1 仍开；不靠下调门槛或 stub 省时间。
