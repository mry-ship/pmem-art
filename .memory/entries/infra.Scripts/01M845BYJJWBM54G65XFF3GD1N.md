---
id: 01M845BYJJWBM54G65XFF3GD1N
module: infra.Scripts
entity: LayerSplitMaeVsSpan
kind: decision
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/compose.py
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆图层不得用 NCC 缩小去追幽灵 MAE，跨度对了比像素差更值钱。
verify: 对比叠回整图与原图：树枝应跨过屋顶；幽灵 MAE 允许高于旧缩放方案。
applies: 道具层合成。背景层不在此取舍内。
aliases:
- 幽灵MAE
- NCC缩小
source:
  kind: conversation
---
取舍：合成阶段用底对齐加 NCC 缩放（树层曾缩到 0.66）可以把幽灵 MAE 压到警告线附近，但会把跨过屋顶的树枝缩短。
改为整帧贴回、scale_mul=1 后，童话花园重跑（assets/mole_garden_resplit）树枝重新跨过花瓣屋顶，池塘为完整椭圆而不是左侧直切；
同时整图幽灵 MAE 从 47.7（警告）升到 53.885（失败线 48）。
各层脏标记只因 layer_ghost_mae 大于 52，content_cut、edge_clip、feat_match 都过。
像素 MAE 量的是重绘笔触差，不能代表主体是否还在裁切框里的原位置。
不要为降 MAE 恢复缩放。
