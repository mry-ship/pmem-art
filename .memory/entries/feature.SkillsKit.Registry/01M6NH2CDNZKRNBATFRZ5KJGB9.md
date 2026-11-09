---
id: 01M6NH2CDNZKRNBATFRZ5KJGB9
module: feature.SkillsKit.Registry
entity: SkillDocAuditFix2_20261105
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#normalize_skill
- skills_kit/skill_specs.py
- docs/skills/flows.html
- build_atlas.py
revision: git:28ae4ac
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 第二轮技能审计落地：清concept幽灵、merge清单去same_object偏、skill别名与dims示例
verify: unittest tests.test_reasonableness_gate tests.test_skill_router；flows无pmem-concept/一档一张默认；normalize
  lens/icon
applies: 改技能文案、reasonableness 别名或 flows/atlas 教学文案后
aliases:
- SkillDocAuditFix2
---
需求来源：玩家第二轮审计。必须保持：
  1) 文案与基准不再提 /pmem-concept（build_atlas、art-atlas、flows、benchmark 改走 /pmem-draw）。
  2) flows/合成梯默认整表一组，非一档一张。
  3) merge 合理性必填改为 chain_mode_declared + upgrade_reason_concrete + family_or_base_lock，不再强 parts_add/base_body。
  4) normalize_skill：lens→shotpack；
裸 icon/图标→icon.unspecified 拒审；
禁止 icon→icon.a。
  5) UI/Icon judge 示例带无瑕疵；
管线合规不进 dims。
  6) 镜头包点选后默认 --skill shotpack。
  7) 外部生图说明 Hook 可能不触发。
入口：skill_specs + reasonableness_gate + flows/build_atlas；
tests.test_reasonableness_gate / test_skill_router。
