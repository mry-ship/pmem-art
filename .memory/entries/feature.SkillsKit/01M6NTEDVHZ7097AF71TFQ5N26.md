---
id: 01M6NTEDVHZ7097AF71TFQ5N26
module: feature.SkillsKit
entity: SkillSpeedCaps
kind: feature
status: active
supersedes:
- 01M6NSWG8QCPGG6SSQQW9T1T02
anchors:
- skills_kit/converge.py#_apply_skill_speed_caps
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 重路径单次审核：生1审1
verify: unittest tests.test_skill_speed_caps tests.test_merge_overview_caps
applies: UI/Icon/merge overview|per_cell/多图分工
---
需求：重路径改为单次审核，并再压缩 UI full kit / Icon 批量 / merge / 多图墙钟。
必须保持：合理性闸；关系说不通不出图；未点名不拆 UI 全家桶；icon 不混档；overview 默认；评分仍写六维与不足。
落地：UI/Icon关键枚/merge overview/per_cell/多图分工 max_rounds=1（生1审1即finish）；
关系稿最多1；
full kit 默认1张总表且禁关键件闭环；
B/C 关键枚默认禁止 converge；
Dark/Tinted 派生；
商业诊断只打字。
适用：上述重路径 converge 会话。
入口：skills_kit/converge.py#_apply_skill_speed_caps + skill_specs + agent_router。
