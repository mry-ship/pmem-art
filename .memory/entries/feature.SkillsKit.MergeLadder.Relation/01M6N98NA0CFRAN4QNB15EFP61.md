---
id: 01M6N98NA0CFRAN4QNB15EFP61
module: feature.SkillsKit.MergeLadder.Relation
entity: MergeReasonableness
kind: feature
status: active
supersedes: []
anchors:
- docs/MERGE_MULTI_LENS.md
- skills_kit/skill_specs.py#pmem-merge-ladder
revision: git:c579c50
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 合成梯通用合理性：过程类型+商业标尺+完成度曲线
verify: MERGE_MULTI_LENS 含§8过程类型与§9铁律；技能五问含过程类型/对标/倒推
applies: 任意 /pmem-merge-ladder 定链与出图前
aliases:
- merge通用合理性
- 过程类型
---
需求来源：建筑链多次自嗨校验仍偏；
需覆盖不限升级展陈的多种merge过程。必须保持：
  1)先对标顶级同品类货柜档序；
  2)先认过程类型A-H（同族形变/同模加装/换物种/原料到成品/生产者/碎片修复/捆扎/多轨）；
  3)合两下可倒推；
未完成到完成；
犒赏材质晚出现；
一链一合同；
机读不等于商业合理。
入口：docs/MERGE_MULTI_LENS.md 与 pmem-merge-ladder 商业标尺闸+五问。
