---
id: 01M70RH6G1W4GW540QQTR6HZXF
module: feature.SkillsKit.MergeLadder.Relation
entity: MergeFamilyGeneDomain
kind: correction
status: active
supersedes:
- 01M70R29MZXZZJ0QMFR9KEN3A7
anchors:
- skills_kit/skill_specs.py#MERGE
- docs/MERGE_MULTI_LENS.md
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 家族基因是店域非纹样；commercial_ref须真链
verify: rg 家族基因口径 .cursor/skills/pmem-merge-ladder/SKILL.md；python3 pmem_art.py merge
  relation-judge --file assets/skill_20261109/merge_overview/merge_phase1_v5.yaml
  --all
applies: 任意 /pmem-merge-ladder 定链与商业审
---
对照 Travel Town Ice Cream/Bread 与画师反馈：合理性翻车根因是把家族基因做成红菇盖贯穿八档，并用自拟烘焙假档序冒充对标。
更正：shop_ladder 家族=同店品类/色相域，允许同店类型跳；
主题锚点可选；
commercial_ref 必须摘竞品真档序可压缩。
已改 skills_kit/skill_specs.py、docs/MERGE_MULTI_LENS.md，并 skills --install；
蘑菇甜点关系重开为 merge_phase1_v5.yaml（冰淇淋盛装曲线）。
推翻此前『改成泡芙→马卡龙贴蘑菇』的纠偏方向。
