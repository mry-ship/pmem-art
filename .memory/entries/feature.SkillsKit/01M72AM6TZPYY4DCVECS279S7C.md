---
id: 01M72AM6TZPYY4DCVECS279S7C
module: feature.SkillsKit
entity: PadReadNotDefect
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/validate_params.py
- skills_kit/data/benchmarks/merge_cabinet.yaml
- skills_kit/data/benchmarks/icon_prop.yaml
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 明确垫图只抽风格、构图和特征，不批垫图不足
verify: 垫图是竖屏时，交付物不再先生成 *__ar_4x3 或 *__ar_16x9 横向填图；brief 里写风格、构图、特征，不写垫图缺点清单。
applies: 玩家明确拿某张图当垫图时。任务是优化那张图本身时，才写它的不足。
aliases:
- 垫图差异
- 竖版出成横版
- 参考图不足
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
玩家指出：参考图是垫图时，要分析它的风格、构图和特征性，不要分析它哪里不足。只有任务是「优化这张图」时，才看垫图的不足。把垫图当缺点清单，成图会和垫图差很远。
证据：Gossip Harbor 商店截图是 1242×2688 竖屏。
本轮把 gh_merge 先填成 3584×2688 横图、把 gh_ui 填成 4780×2688 横图，再按 2×4 整表和 16:9 界面出图。
合成三张都是 1152×864，界面是 1280×720。
原画和克隆是 864×1152 竖幅，图标母版是方形，跟对应垫图。
同时 brief 写了「只锁光泽，不抄棋盘、龙虾、厨房」，把垫图的构图和道具语言当成禁止项。
必须保持：玩家点名垫图时，先写风格、构图（含竖横）和特征，画幅跟垫图；不要先把竖图填成横画布。不足只写在「优化这张图」的任务里。
