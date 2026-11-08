---
id: 01M6YDZ9G75M6GPQC90QG6DRXB
module: feature.SkillsKit
entity: SkillRoundCap4
kind: feature
status: active
supersedes:
- 01M6NTZBEWHRW1PXC3GXFD393R
anchors:
- skills_kit/converge.py#_apply_skill_speed_caps
- skills_kit/skill_specs.py
- skills_kit/agent_router.py
revision: git:6a2d5af
author: yanghu
note_date: '2026-11-09'
summary: 重路径恢复最多4轮到线即停+merge逐格并行
verify: python3 -m unittest tests.test_skill_speed_caps tests.test_merge_overview_caps
  tests.test_skill_router -q
applies: UI/Icon/merge/多图 converge 轮次与 merge 逐格出图
---
需求来源：用户 2026-11-09 要求①部分技能只跑一次出图就停，改成4轮；②merge 单张（per_cell）串行太久，改并行生图。
必须保持：合格线 ≥9.5 到线即停；关系稿最多 2；未点名逐格仍默认 overview_sheet；普通图合同不变；showcase-gate 对满轮/安全早停仍认。
落地：
1) skills_kit/converge.py：MERGE/UI/ICON/SPLIT_*_MAX_ROUNDS=4；
   取消这些路径 single_judge 硬顶；
   stop_policy 回 dynamic_threshold（overview 仍 merge_overview_checklist）。
2) skill_specs / agent_router / install 文案：出图一轮交件 → 最多4轮·到线即停；per_cell 强制各档并行独立 session，禁止串行等完一档再开下一档。
3) 测例：tests.test_skill_speed_caps / test_merge_overview_caps / test_skill_router。
入口：converge start 套 caps；/pmem-ui /pmem-icon /pmem-merge-ladder / 多图分工。
