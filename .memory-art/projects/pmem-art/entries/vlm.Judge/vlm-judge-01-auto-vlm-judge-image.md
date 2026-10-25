---
id: vlm-judge-01
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 审图只接受五维观察、文件头和可选 sidecar，不评模型价格，也不采信手填总分
---
`auto_vlm_judge_image` 根据构图、光影、透视解剖、质感、风格五项计算加权分。它读取图片宽高与可选的 `.vlm.json`，不把 API 价格、中文理解或供应商对比算进画面分。五维解析成功后，手填 `--score` 不参与停机。
