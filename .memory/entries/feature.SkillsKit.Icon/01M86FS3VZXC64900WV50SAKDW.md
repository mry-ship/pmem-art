---
id: 01M86FS3VZXC64900WV50SAKDW
module: feature.SkillsKit.Icon
entity: IconCropWins
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/prompt_scale.py#drop_opposed_injections
- skills_kit/reasonableness_gate.py#_icon_a_store_default_issues
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 图标裁切压过档位锁，厚体积不再被压成哑光
verify: pyw -3 -u -m unittest tests.test_prompt_conflict tests.test_reasonableness_gate
  -q
applies: icon.a 从零出桌面图标
source:
  kind: code
---
需求来源：玩家要顶级 app icon，tilematch-icon-store 正式分停在 7.30。
必须保持：icon.a 修订句写「底色只留在四角」或「外轮廓被四边裁到」。
好几张相同物件咬成一个符号，这一团一起被画面裁到。
正文有软卡通厚体积、冷暖相反或高饱和时，生图词去掉「避免过饱和」。
正文有撑满、占比或四边裁时，去掉「不改机位」和「不做整体 recompose」。
适用：icon.a 从零出桌面图标。
入口：reasonableness_gate 的图标默认句；prompt_scale.drop_opposed_injections。
