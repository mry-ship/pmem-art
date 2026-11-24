---
id: 01M86FTMMNGR4ENWW6889ERNBZ
module: feature.SkillsKit.Converge
entity: IconEmptyRefPadsBest
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py
- skills_kit/reasonableness_gate.py
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 图标无参考时垫最高分，留白超过约 6% 就继续裁
verify: python -m unittest tests.test_converge_guards.TestPadAuto.test_icon_a_without_style_ref_pads_best_plate
  tests.test_converge_guards.TestPadAuto.test_icon_crop_note_flags_stage_inside_the_old_band
  tests.test_prompt_conflict.BriefBeatsInjectionTests.test_icon_continuation_releases_the_stage
  -q
applies: route 含 icon.a 且 ref_image 为空
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
  kind: code
---
需求来源：口头参考竞品不会变成垫图，第 2 轮整段重画会丢边框；外接框过了 72% 仍是四周一圈舞台。
必须保持：route 含 icon.a 且没有风格参考图时，第 2 轮垫最高分成图，只改裁切。
续写句写明四周留白不算要保持的内容，外轮廓可以顶到四边；主体、配色和边框保持垫图。
已有风格参考图时仍垫那张参考。
任一边缘留白超过约 6% 时，下一轮改点写上量到的四边留白，并要求外轮廓被四边裁开、底色只留在四角。外接框短边过了 72% 不算已经裁满。
适用：icon.a。9.5 不降，安全早停仍在。
入口：converge._resolve_pad_auto、_icon_crop_note；
prompt_scale.compose_continuation_prompt 的 release_margin、icon_stage_margins。
