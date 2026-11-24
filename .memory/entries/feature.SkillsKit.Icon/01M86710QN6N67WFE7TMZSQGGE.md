---
id: 01M86710QN6N67WFE7TMZSQGGE
module: feature.SkillsKit.Icon
entity: ScoreThreeCauses
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#apply_hurdles
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 低分是安全区门槛；主体、空垫图、相反提示词各管一块
verify: tilematch-icon-face 正式分 7.20/7.60/7.90，安全区同数；ref_image 为空
applies: 桌面图标正式分被安全区替换，且最终提示词同时含简报和口味包
aliases:
- 分数低
- 提示词太长
source:
  kind: conversation
---
正式分低，是因为图标门槛把正式分改成了安全区这一维。tilematch-icon-face 三轮安全区 7.2、7.6、7.9，都低于 8，正式分就是这三个数。识别度和色板过了 8，加不进正式分。
三件事各管一块。
分析把游戏写成「一枚牌加一颗金星」，成图就按这句画成徽章。
ref_image 为空且 pad=auto，三轮都不垫图，文字里的 76% 量出来只有约 66% 到 71%。
最终提示词把简报里的「高饱和、撑满」和口味包里的「避免过饱和、柔光、不改机位」接在同一条里，后两轮只是再贴一遍放大，没有拆掉前一句，宽度几乎不动。
