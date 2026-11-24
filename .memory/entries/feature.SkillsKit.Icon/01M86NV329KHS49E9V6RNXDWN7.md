---
id: 01M86NV329KHS49E9V6RNXDWN7
module: feature.SkillsKit.Icon
entity: IconReleaseMarginRewritesPlate
kind: correction
status: active
supersedes:
- 01M86NF4BT8GQSN8PBEGCAWMCT
anchors:
- .cursor/skills/pmem-icon/SKILL.md
- .agents/skills/pmem-icon/SKILL.md
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 续轮一律放行外轮廓，预烤白角会被整张重画拆掉
verify: 对照 prompt_scale.compose_continuation_prompt 的 release_margin 句，以及 tilematch-icon-rerun
  第2轮定稿仍含「三张草莓棋面和块面高光留住」
applies: icon.a 无风格参考、第 2 轮垫最高分成图时
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
tilematch-icon-rerun 第 2 轮提示词已经写了「三张草莓棋面和块面高光留住」，棋槽仍然被拆掉。根因不是改点漏写棋面。
无参考图标的续轮一律加「四周留白不算要保持的内容，外轮廓顶到四边」。第 1 轮四边中点已是蓝底，icon_stage_margins 为 0，自动裁切句是空的。四个白角是预烤圆角切出来的，不是主体四周的舞台。
这句把外轮廓标成可以重做。生图是整张重画。模型要一块直角蓝底时，把圆角底板和棋槽一起拆掉，只留三颗草莓，并加上投影。安全区 7.6，正式分 7.60，STOP_REGRESSION。
旧结论说只要改点里同时写下棋面就能保住。这次改点写了，仍没保住。
