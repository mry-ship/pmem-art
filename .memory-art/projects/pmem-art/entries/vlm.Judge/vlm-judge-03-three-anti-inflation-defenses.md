---
id: vlm-judge-03
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 防虚高靠加权重算、短板词和硬伤词；生成与审图分两步，本函数不调用第二套模型
---
生成走 `converge generate`，审图走 `converge judge`。`converge step` 会直接拒绝。防虚高的三件事是：五维加权覆盖手填分、短板词把分压到 8.90 以下、多手或多肢体把分压到 7.90 以下。否定句（未出现、无、并非、非数字化）不算命中。另加物理图闸门：缺图/纯色不可达标。
