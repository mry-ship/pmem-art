---
id: 01M72PJES5JM6H333D1CFNRNFV
module: feature.SkillsKit.MergeLadder.Relation
entity: VolumeLadderGateFail
kind: correction
status: active
supersedes:
- 01M72JKSJMA3N029CNC4JG2XX9
anchors:
- skills_kit/merge_relation.py#audit_overview_sheet
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 三张链卡在框高闸是闸门错了，不是身份链不稳
verify: audit_overview_sheet 对近邻框高接近返回 ok=True 且带「提示：」
applies: GH 竖屏合成梯回顾旧会话失败原因时
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
旧结论把果酱/浇水/管乐未过9.5主要归因于邻档框高差与末档非最大。根因是体量硬闸与竞品相反，逼出拼贴过闸；管乐拼贴版还曾被判9.51。
闸门已降为提示（见 Delivery/VolumeGateSoft）。后续收敛应查剪影/件数可分、拼贴残片切顶、浅色卡，而不是抠格凑 0.04 阶梯。
