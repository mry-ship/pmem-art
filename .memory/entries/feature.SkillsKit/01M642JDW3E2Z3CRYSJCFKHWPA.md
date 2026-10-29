---
id: 01M642JDW3E2Z3CRYSJCFKHWPA
module: feature.SkillsKit
entity: GroupSheet
kind: decision
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py
- skills_kit/skill_specs.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 合成梯用整组16:9正方形格生成再切开，不为锁色而一档一张散跑
verify: 组图按 2x4 相同正方形格切开后各档完整不穿格
applies: 关系讨论过关后的合成梯出图
---
选整组 16:9（8 个相同正方形格）交给生图模型再 split-sheet，而不是一档一张散跑，是为了锁同一机位、同一棚灯、同一画风管线；
共享的是镜头和灯，不是色相和材质。
合成链对标商业 merge-2：类型相似就够，用 merge_why 解释换件，而不是同一物件反复加零件。
代价是切线必须落在格缝上，切进邻件要只重出那一档。
