---
id: 01M6NTZBEWHRW1PXC3GXFD393R
module: feature.SkillsKit.Converge
entity: SkillSpeedCaps
kind: feature
status: active
supersedes:
- 01M6NTEDVHZ7097AF71TFQ5N26
- 01M6NS7144XMS7048P9MNK22G3
- 01M6NS7F2BG7M3DN1Z9BVTHM6K
anchors:
- skills_kit/converge.py#_apply_skill_speed_caps
- skills_kit/skill_specs.py
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 出图一轮交件语义统一+关系回2+检测收窄
verify: unittest tests.test_skill_speed_caps tests.test_merge_overview_caps tests.test_skill_router
applies: UI/Icon/merge/多图/普通图合同与 CLI 硬顶
---
需求：审计不合理点落地。
必须保持：未点名逐格仍默认整表；出图重路径生图轮次=1；≥9.5 仍是过线标尺。
落地：
  1) 关系稿最多2（第1过即停）；
  2) 交件统一为「出图一轮交件+标明过线/未过线」，废除与「必须≥9.5才算交」的冲突措辞；
  3) 删除整表垫上一张/条件重出死合同；
  4) 普通图改为到线即停、最多4兜底，去掉「禁止只生一张/强制4轮」；
  5) per_cell 仅点名；
  6) 收窄 UI/merge/icon 误套检测；
  7) Icon A 默认只交 Light，禁假齐套三态；
  8) 命名改为出图一轮交件（只限生图轮次）。
