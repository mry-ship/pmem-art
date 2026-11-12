---
id: 01M75FD1JCYHMCGFWY0KQR9Z7Q
module: feature.SkillsKit
entity: StyleSourcePriority
kind: correction
status: active
supersedes:
- 01M7272AM9MJCM96RE3V4AZDM8
anchors:
- skills_kit/install.py
- docs/COMMERCIAL_BENCHMARK.md
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: merge缺省气质改为GH玩具货柜软渐变
verify: .cursor/rules/pmem-art.mdc 含「玩具货柜手绘软渐变」且不含「光泽卡通 3D」
applies: 普通图/原画/UI/图标A·C/合成梯都没有文字风格时；仅 merge 钉 GH
aliases:
- 手绘软渐变
- GH玩具货柜
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
旧文案把休闲 merge 缺省写成 Gossip Harbor「光泽卡通 3D」。
更正：缺省钉 Gossip Harbor **玩具货柜手绘软渐变**（圆润厚实、无硬描边、暖饱和、柔光糖釉；禁硬镜面 CGI）。风格优先级仍是文字>参考>品类默认；非 merge 仍禁止套 GH 货柜。
细则与注入锁句在 feature.SkillsKit.MergeLadder（MergeStyleDefault）。
