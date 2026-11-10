---
id: 01M72XC49AZP6YDHRMT4MJMQKX
module: feature.SkillsKit.MergeLadder.Delivery
entity: PeelCardMeasure
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/merge_relation.py#_soft_card_shadow_mask
- skills_kit/merge_relation.py#_cell_fragment_rows
- skills_kit/merge_relation.py#_cell_subject_height_ratio
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 剥卡后去同色相暖影；残片双路径召回贴边块
verify: py -3 -m unittest tests.test_delivery_gates
applies: merge overview_sheet 含浅色卡或拼贴验收时
aliases:
- 暖色投影量进框高
- 管乐残片漏检
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
需求：浅色圆角卡整表要量物件不是卡；还要抓住贴边拼贴残片。
必须保持：
1) 柔影按「与卡纸同色相、更暗」剔除（暖桃色投影 chroma>30 也能去），不再要求 chroma<30。
2) 若去影把实心物件切碎（最大连通域面积 < 全 mask 55%），框高改用行占用最长带。
3) 残片取剥卡 mask 与格缝 mask 的较大值；只忽略很薄且整段落在外圈的碎带，有面积的贴边块必须可抓。
4) 末档明显矮用两位小数比较，避免 0.081 vs 0.08 浮点擦边。
验收：sheet_r1 L2/L8 ∈[0.65,0.85] 且 ok=True；管乐/果酱拼贴 final ok=False（管乐 L6≈0.041）。
入口：merge_relation._soft_card_shadow_mask / _cell_subject_height_ratio / _cell_fragment_rows。
