---
id: 01M86JTCS7E6YT02D5N9JTHHJQ
module: feature.SkillsKit.Icon
entity: IconPadIgnoresCrop
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_icon_crop_note
- skills_kit/prompt_scale.py#icon_subject_span
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 垫最高分成图并写裁到四边，生图仍把主体留在中部
verify: 重跑 icon.a 无风格参考闭环，看第 2 轮是否 pad=icon_best，再量 icon_subject_span 短边是否仍停在 80%
  出头而四角仍是大块底色
applies: icon.a 且没有风格参考图、用垫最高分成图只改裁切的轮次
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
tilematch-icon-top：图标无风格参考时第 2 轮起垫最高分成图，提示词写明外轮廓被四边裁到、底色只留四角。
GenerateImage 仍把三张棋面留在画面中部，短边外接框从 77% 只到 83%，棋缝没并掉，糖釉只出现在草莓上，棋面仍是哑光。
量到短边≥72% 不会自动写裁切句。
不要把「垫图只改裁切」当成已经裁到四边。
会话 tilematch-icon-top 最高 8.73，未过 9.5。
