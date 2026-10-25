---
id: vlm-judge-06
module: vlm.Judge
kind: pipeline_constraint
status: active
note_date: '2026-10-25'
verified: '2026-10-25'
author: pmem-art
summary: 达标停机要同时满足加权分、本档 prompt 指令和改动幅度上限
---
`STOP_TARGET_REACHED` 除了加权分达到档位阈值，还要求：磁盘上有真实有效图（物理闸门）、已记录的生成 prompt 含有本档 directive。相邻两轮正文改动超过 `max_prompt_delta_ratio` 时不能停机。硬伤词或画幅超差（相对误差大于 15%，或横竖颠倒）会先把分数压下去。`finish` 只把同时过分数与物理闸的轮次算作达标。
