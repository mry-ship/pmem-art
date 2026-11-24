---
id: 01M865KCMYX1EWA7RRNWKZSB1Y
module: feature.SkillsKit.Icon
entity: IconAGameRead
kind: correction
status: active
supersedes:
- 01M863GQDVXF3YY9PC5YGDJ6XC
anchors:
- skills_kit/reasonableness_gate.py#_icon_a_game_read_issues
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 一枚星牌是徽章，不是 Tile Match 的配牌
verify: tilematch-icon-face 三轮都是一枚奶油牌加金星，胜出 7.90
applies: icon.a 点了三消或 Tile Match，闸门要求一枚牌面时
aliases:
- 一枚牌面
- 金星
source:
  kind: conversation
---
把三消桌面图标收成「一枚超大牌面加一颗星」是写错的游戏。
Tile Match 是把花色相同的几张牌配成一组消掉。
一枚奶油圆角牌加一颗金星，读出来是一枚徽章。
闸门现在只放行「一枚牌面加可配花色」这一种句子，多张能对上的牌、以及这个游戏自己的角色，都会被拦。
tilematch-icon-face 的三轮成图就是按这句画的。
分数是另一件事：牌宽约 71%，安全区低于 8，正式分改取该维；
分数还在涨，早停不触发，三轮都跑完。
