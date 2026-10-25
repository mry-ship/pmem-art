---
id: vlm-judge-07
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 缺图、边长过小或字节熵过低时禁止达标，finish 不得写入达标 recipe
---
`auto_vlm_judge_image` 默认 `require_image=True`：磁盘无文件、边长 `< 64px` 或 `color_entropy < 3.2`（纯色占位）时 `passed=False`，分数硬顶到阈值以下。`converge generate` 拒绝登记无效输出。`_round_counts_as_passed` / `finish` 要求：`judged=True`、分数达线、无 gate 拦截，且对路径**现场** inspect（不信任缓存 verification）。
