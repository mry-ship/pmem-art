---
id: 01M77SDZSKVV9R72YGC1CDP9W9
module: feature.SkillsKit.MergeLadder
entity: MergeStyleDefault
kind: correction
status: active
supersedes:
- 01M75JZVKXPGD7KSMPF54XEWGC
anchors:
- skills_kit/merge_relation.py#_MERGE_SURFACE
- improve/warm_start.py#_MERGE_CONFLICT_TASTE
- docs/GOSSIP_HARBOR_MERGE.md
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: GH缺省改回软立体糖釉；平面货柜是矫枉过正
verify: merge_surface_lock_line 含软立体糖釉、不含平面货柜感；unittest delivery_gates+warm_start
  过
applies: 休闲merge未点名其它画风时
aliases:
- 硬料
- 软立体糖釉
- 平面货柜矫枉过正
---
玩家指出「平面货柜感+禁任何3D」与真 Gossip Harbor 不搭。真GH棋盘货是软立体糖釉玩具货柜（有体积、柔光釉面），不是绘本平涂贴纸。
根因：为躲Cursor黏土软塑胶，把「禁劣质黏土UI」写成「禁一切3D」，名义GH、实际偏平面。
更正：_MERGE_SURFACE 钉软立体糖釉；禁硬镜面CGI/皮克斯硬塑/哑光黏土软塑胶UI/平面绘本贴纸冒充；Warm-Start 冲突表改拦平面货柜/黏土渲染，不再拦软立体糖釉正信号。
