---
id: 01M86NF4BT8GQSN8PBEGCAWMCT
module: feature.SkillsKit.Icon
entity: IconCornerFixDropsSymbol
kind: conclusion
status: active
supersedes: []
anchors:
- .cursor/skills/pmem-icon/SKILL.md
- .agents/skills/pmem-icon/SKILL.md
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 只改四角白边会把棋面符号拆回漂着的水果
verify: tilematch-icon-rerun 第1轮 8.65、第2轮 7.60，STOP_REGRESSION
applies: icon.a 续轮只改四角白边或预烤圆角时
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
tilematch-icon-rerun：第 1 轮 8.65，蓝底顶到四边，三张草莓在棋槽里，高光成块，四角是白的预烤圆角。
第 2 轮改点只写收掉白边、蓝底铺进直角。
成图棋槽消失，三颗草莓漂在蓝底上并带投影，四边留白左12%右11%上9%下14%，安全区 7.6，正式分 7.60，STOP_REGRESSION，交付第 1 轮。
收白边不能单独当改点，续写必须同时留下棋面边框和咬合符号。
