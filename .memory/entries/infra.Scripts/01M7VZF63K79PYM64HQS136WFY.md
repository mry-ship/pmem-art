---
id: 01M7VZF63K79PYM64HQS136WFY
module: infra.Scripts
entity: LayerSplitPlanBoxes
kind: exclusion
status: active
supersedes: []
anchors:
- .cursor/skills/pmem-layer-split/SKILL.md
- assets/viking_camp_10/_crops_guide.png
- assets/viking_camp_10/_crops/spear_rack.png
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 禁止为降asp_err收框；框偏小切肢优先扩边
verify: SKILL §1.1 改为先包全再留垫；禁止为 asp 收框；viking _crops/spear_rack 矛顶贴边可复现
applies: 拆层定块与改脚印时
aliases:
- 框太小
- 切肢
- 收框
- pad
source:
  conversation: b7b56b1c-a3f6-44a5-8249-75cbf838c588
---
玩家反馈框选总偏小。viking_camp_10 guide/crops 证实：枪架矛顶贴边、盾只露上沿、灯柱底被切、女猎人靴/披风留白不足。
错误路径：R2 为降 asp_err 把框裁矮/裁窄 → 更切肢 → isolate 换样。
正确：先包全外轮廓，再 pad 至少 0.02～0.04（柔边可 0.05）；主体顶到 crop 边=太小，只扩该边；asp/fill 不过重抽精灵，禁止收框凑比例。
与「禁止为 fill 撑框」并存：过小扩、过宽禁撑到吞槽。
