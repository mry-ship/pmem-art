---
id: 01M6NVRWDY4YC3T682VEJ3NC49
module: feature.Improve
entity: MemoryHygiene
kind: feature
status: active
supersedes: []
anchors:
- improve/memory_hygiene.py#run_hygiene
- improve/knowledge.py#cmd_learn
- pmem_art.py#hygiene
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 记忆卫生一键清理；hygiene 默认不收 learn
verify: pyw -3 -u -m pytest tests/test_memory_hygiene.py tests/test_warm_start_guardrails.py
  -q
applies: doctor/list/validate/sync 与 pyw -3 -u pmem_art.py hygiene [--accept-learn]
---
按文字为主模型优化：
  1) 缺图不再标内容 STALE，记 asset_gaps；
role=detached 跳过 QA。
  2) sync/hygiene 过滤噪声 candidates。
  3) list 默认隐藏空壳。
  4) doctor 硬/软分流。
  5) hygiene：detach、补 specs、taste 去重、归档 converge report（可逆提示）；
默认 accept_learn=False；
仅 --accept-learn 且 stash_only 消费 learn_proposals；
accept 后清空/扣减队列。
对齐 AGENTS：知识卡须明确收下。
