---
id: 01M6NHNJ2XKS2NHWA4P4DQZ8QV
module: feature.SkillsKit.Registry
entity: SkillDocAuditFix3
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#_bundle_score
- skills_kit/route_gate.py#check_route_gate
- skills_kit/skill_registry.py#slice_markdown_section
- skills_kit/reasonableness_gate.py#normalize_skill
revision: git:28ae4ac
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 第三轮技能审计硬修：Icon节裁/无瑕疵硬闸/合成梯交付库/别名/点名种闸
verify: unittest skill_router/route_advise named_seed/reasonableness aliases/param_validation
  geometric+soft；route bank 整表/per_cell 可检索
applies: 改技能文案、评分、route 闸或 reasonableness 别名后
---
第三轮审计确认项落地：
  1) Icon 按 heading 裁节须跳过围栏内井号（slice_markdown_section）并去掉 Mode B bash 伪 H1；
Mode A/B/C 并列。
  2) UI/Icon 计分缺无瑕疵时 weighted_score=None（不再可选附件）。
  3) route_bank+CANON 补整表/overview/per_cell。
  4) reasonableness 别名覆盖镜头/draw.lens/多图/合成/UI kit/route_id。
  5) converge 缺 route 时可 --route-id 点名种闸（不必 skip）。
concept 仅保留 retired 测试清理。
