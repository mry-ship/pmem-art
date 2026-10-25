---
id: vlm-judge-02
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 五维一旦解析成功，校准分就是加权分，不再给手填总分留 0.15 的上浮
---
`parse_5d_dims` 按当前档位权重计算总分。加权分存在时，校准分等于加权分。技能旧格式 `风格/结构/光影/合规/还原` 按 2.5+2.5+2.0+1.5+1.5 相加。解析失败时本轮记 0，不回退手填分。
