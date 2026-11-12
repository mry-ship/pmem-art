---
id: 01M75FCVQ2NAH1C8RQPQKQJRPQ
module: feature.SkillsKit.MergeLadder
entity: MergeStyleDefault
kind: correction
status: active
supersedes:
- 01M72ZXNMSR0H7P0FFCGRH6ZQD
anchors:
- skills_kit/merge_relation.py#_MERGE_SURFACE
- docs/GOSSIP_HARBOR_MERGE.md
- docs/COMMERCIAL_BENCHMARK.md
- skills_kit/data/benchmarks/merge_cabinet.yaml
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: GH默认词去掉「卡通3D」，改手绘软渐变货柜
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_merge_without_style_is_gossip_harbor；默认锁含「手绘软渐变」且不含「光泽卡通
  3D」
applies: 休闲 merge 未点名其它画风时
aliases:
- 手绘软渐变
- 禁硬卡通3D
- GH玩具货柜
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧默认锁/对标句写「光泽卡通 3D」，引擎常执行成硬镜面 CGI 图标；真 Gossip Harbor merge 货柜是手绘软渐变糖釉道具。
更正：休闲 merge 缺省钉 Gossip Harbor **玩具货柜**（手绘软渐变、圆润厚实、无硬描边、暖饱和、柔光糖釉）；显式禁止硬镜面 3D / 硬卡通 3D / 皮克斯硬塑胶高光。
GH 就是本类 merge 默认渲染，不是「先选卡通3D再碰巧像GH」。
已改：merge_relation._MERGE_SURFACE、COMMERCIAL_BENCHMARK、GOSSIP_HARBOR_MERGE、merge_cabinet.yaml、skill_specs、install 规则与已安装技能。
