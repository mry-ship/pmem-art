---
id: 01M75JZVKXPGD7KSMPF54XEWGC
module: feature.SkillsKit.MergeLadder
entity: MergeStyleDefault
kind: correction
status: active
supersedes:
- 01M75FCVQ2NAH1C8RQPQKQJRPQ
anchors:
- skills_kit/merge_relation.py#_MERGE_SURFACE
- improve/warm_start.py#_MERGE_CONFLICT_TASTE
- .memory-art/projects/pmem-art/_profile/taste.json
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: GH缺省禁任何软/硬3D；taste不得再正强化卡通3D
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_merge_without_style_is_gossip_harbor
  + TestMergeConflictTaste；merge_surface_lock_line 含软卡通 3D/黏土拟态；filter_keeps 不含糖釉卡通3D、含平面货柜
applies: 休闲 merge 未点名其它画风时；Warm-Start 向 merge.* 注入 keep/habit 时
aliases:
- 软3D
- 黏土图标
- 糖釉卡通3D
- 平面货柜感
source:
  conversation: fda824e5-6393-4f0c-859e-6a0bf93b50bd
---
前次更正只去掉默认锁里的「光泽卡通 3D」，仍只禁硬镜面/硬卡通 3D；taste keep 仍正强化「糖釉卡通3D」，Warm-Start 每轮灌进 converge，Cursor 落成黏土软塑胶轻 3D。
更正：
  1) _MERGE_SURFACE 改为手绘软渐变平面货柜感，材质锁死手绘糖釉，显式禁止软卡通 3D/糖釉卡通3D/光泽卡通3D/黏土拟态/软塑胶 UI/立体渲染图标；
  2) warm_start._MERGE_CONFLICT_TASTE 拦截含「卡通3D/光泽卡通/黏土渲染/glossy cartoon 3D」的 keep/habit，禁止再注入；
  3) taste keep/style 改写为平面货柜正信号。
技能/文档/规则同步：skill_specs、pmem-merge-ladder、GOSSIP_HARBOR_MERGE、COMMERCIAL_BENCHMARK、merge_cabinet、CLAUDE/AGENTS/pmem-art.mdc。
