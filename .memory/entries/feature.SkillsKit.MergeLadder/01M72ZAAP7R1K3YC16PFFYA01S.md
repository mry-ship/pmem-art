---
id: 01M72ZAAP7R1K3YC16PFFYA01S
module: feature.SkillsKit.MergeLadder
entity: MergeStyleDefault
kind: correction
status: active
supersedes:
- 01M72Z208C808YQW9FS6M5S5ZH
anchors:
- skills_kit/merge_relation.py#merge_surface_lock_line
- skills_kit/delivery_gates.py#generate_prefix
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 点名风格只看 goal；Warm-Start「赛博」不得关默认锁
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_merge_without_style_is_gossip_harbor（goal无点名+prompt含赛博霓虹须注入完整锁）
applies: 休闲 merge 合成梯、玩家 goal 未点名其它画风时
aliases:
- 赛博误关锁
- Warm-Start踩点名
- player_named_style
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
真跑 jam 第1/2轮 merge_surface_lock_line 长度仍为 0，generate_prefix 未加锁句。
根因不在完整硬句跳过（那一层仍成立），而在更上游：player_named_style(goal+prompt) 扫到 Warm-Start「个人禁用习惯」里的「赛博霓虹/霓虹紫」，词表 _STYLE_OPT_OUT 含「赛博」，被当成玩家点名赛博，整段默认锁留空。
只看 goal 为 False，只看 prompt 为 True，命中词仅「赛博」。
现改为：点名风格只看 goal；是否已含完整硬句才看 prompt。taste「避开赛博」不再误关锁；goal 写水彩/写实仍留空。
更正：此前怀疑「棋盘缩略」触发跳过不成立；真正触发是「赛博」。完整硬句跳过条件仍保留。
