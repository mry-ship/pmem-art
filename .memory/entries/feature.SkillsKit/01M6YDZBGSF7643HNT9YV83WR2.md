---
id: 01M6YDZBGSF7643HNT9YV83WR2
module: feature.SkillsKit
entity: SkillSpeedCaps
kind: correction
status: active
supersedes:
- 01M6NTZBEWHRW1PXC3GXFD393R
anchors:
- skills_kit/converge.py#_apply_skill_speed_caps
- skills_kit/skill_specs.py
revision: git:6a2d5af
author: yanghu
note_date: '2026-11-09'
summary: 重路径不再强制出图一轮交件，改最多4轮
verify: python3 -c "from skills_kit.converge import MERGE_OVERVIEW_MAX_ROUNDS,MERGE_PER_CELL_MAX_ROUNDS,UI_CONCEPT_MAX_ROUNDS,ICON_KEY_MAX_ROUNDS,SPLIT_MAX_ROUNDS;
  assert all(x==4 for x in (MERGE_OVERVIEW_MAX_ROUNDS,MERGE_PER_CELL_MAX_ROUNDS,UI_CONCEPT_MAX_ROUNDS,ICON_KEY_MAX_ROUNDS,SPLIT_MAX_ROUNDS))"
applies: converge 重路径轮次硬顶
---
旧结论：UI/Icon/merge/多图为出图一轮交件（max_rounds=1、single_judge）。
更正：上述路径恢复与普通图一致——≥9.5到线即停，最多4轮兜底；取消 start 时写入 single_judge。
关系稿上限仍为2。merge per_cell 合同改为各档并行独立 session 生图。
