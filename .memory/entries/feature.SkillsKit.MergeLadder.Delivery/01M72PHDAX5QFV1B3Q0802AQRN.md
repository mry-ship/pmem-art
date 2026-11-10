---
id: 01M72PHDAX5QFV1B3Q0802AQRN
module: feature.SkillsKit.MergeLadder.Delivery
entity: VolumeGateSoft
kind: correction
status: active
supersedes:
- 01M72MVDQG54HMDDT38K49EVTP
anchors:
- skills_kit/merge_relation.py#audit_overview_sheet
- skills_kit/delivery_gates.py#overview_sheet_hints
- skills_kit/converge.py
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 整表体量闸降为提示；只硬拦末档明显矮与缺主体
verify: py -3 -m unittest tests.test_delivery_gates tests.test_merge_relation
applies: 休闲 merge overview_sheet 交件与关系稿 scale_pct
aliases:
- 体量闸
- 框高阶梯
- 拼贴整表
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
对标 Gossip Harbor Decaf Coffee：主体占卡高不单调，邻档常接近，分档靠剪影/件数。
原先 audit_overview_sheet 要求邻档框高每档 +0.04 且末档最大，竞品过不了，还逼出跨轮抠格拼表（残片/切顶）。
已改：邻档框高接近与末档略非最大只出「提示：」；
硬伤仅缺主体、末档比全表最高矮超过 OVERVIEW_LAST_SHRINK(0.08)。
judge_gate_notes 只收硬伤；
overview_sheet_hints 把提示写入 defects/audit_warnings 但不打回。
converge 的 next_fix 改为「末档不得明显矮；
靠剪影/件数；
禁止跨轮抠格拼表」。
yaml scale_pct 也不再要求单调递增。
benchmarks/merge_cabinet.yaml 与 ANALYSIS 尾部已去掉「体量缓增/框高阶梯过线」口径。
