---
id: 01M86PNP7S1CZ6B6ZQ4WRPNQ47
module: feature.SkillsKit.Icon
entity: IconIdentityBanActivatesSubject
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_ICON_IDENTITY_BAN_RE
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 不要国王会把国王写进图
verify: unittest tests.test_reasonableness_gate.TestReview.test_icon_a_identity_ban_fails
applies: icon.a 参照别的商店图标只取完成度时
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
参照别的商店图标时，把「不要国王、不要王冠、不要胡子」写进修订句和锁，生图会把这些词当成要画的东西。tilematch-icon-rerun 的锁里就有不要国王。玩家指出这类排斥句堆多了，成图会变差。
英雄写它是什么。参照只取完成度：冷底、四边裁开、一块材料、高光成块、一主光。不要把对方的角色写进提示词。
