---
id: 01M7PQ001FWB4DN6FK3AMT5QHF
module: feature.SkillsKit.Registry
entity: PackMissedClickTable
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/skill_registry.py#_draw_pack_headings
- skills_kit/skill_registry.py#_icon_routes
revision: git:fdcc718
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 可点轮次表写在执行包没带走的第二节，界面图标合成梯会漏交
verify: slice_route_body 对 draw.ordinary、ui.kit、merge.ladder、icon.a 含「轮次单图表」
applies: 改技能结算文案或 pack_headings 时
verified: '2026-11-20'
verified_at: '2026-11-20T17:02:25.781+08:00'
---
现象：同一套闭环里，有的技能结算会贴可点轮次表和过程拼板，界面、图标、合成梯经常不贴。
原因：双主交件的具体步骤写在 draw 的「## 二、」Step 3。
执行包在有执行卡时不再塞整节二。
ui.kit 的 pack 只有执行卡；
merge 的 pack 是执行卡加禁止；
icon 只靠记忆静默里一句「过程图 JPG + 全轮履历」，没要求 Read process_sheet，也没要求贴 Markdown 轮次表。
影响：总控按 pack 交给执行侧时，这些支路不会按拼板+可点表结算。
以后改结算文案，要写进出图 route 的 pack_headings（现在是「## 交件可见」），不能只写在没被打包的第二节。
