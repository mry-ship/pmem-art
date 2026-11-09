---
id: 01M6NSWG8QCPGG6SSQQW9T1T02
module: feature.SkillsKit.Converge
entity: SkillSpeedCaps
kind: feature
status: active
supersedes:
- 01M64C0D8Z5H0Q3GXX1QT779D6
anchors:
- skills_kit/converge.py#_apply_skill_speed_caps
- skills_kit/skill_specs.py
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: UI/Icon/per_cell/draw 保质压缩轮次
verify: unittest tests.test_skill_speed_caps tests.test_merge_overview_caps
applies: pmem-ui / pmem-icon / merge per_cell / pmem-draw 出图会话
---
需求：在质量仍≥9.5 / 清单过关前提下，压缩最重 skill 墙钟。
必须保持：到线即停；合理性闸；merge 关系说不通不出图；UI 未点名不拆全家桶；icon A/B/C 不混；overview 默认。
落地：
1) UI：默认 concept-only；概念 CLI max_rounds≤3；组件表≤2 轮且默认≤2 张 sheet；关键件二次收敛默认跳过（<9.0/硬伤才 1 轮）。
2) Icon：B/C 关键枚闭环默认可选；开则≤2 轮；A 三态默认派生，翻车再单开。
3) merge per_cell：每档硬顶 2 轮（仍≥9.5）；关系仍最多 2 稿。
4) draw：Best-of-N 默认禁止。
入口：skills_kit/converge.py#_apply_skill_speed_caps + skill_specs + agent_router + skills --install。
