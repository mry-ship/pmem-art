---
id: 01M83Q3M675YXGSNXHKDXQYR10
module: feature.SkillsKit.Atlas
entity: ClassifyWatchBatchResilience
kind: correction
status: active
supersedes: []
anchors:
- classify.py#cmd_watch_sync_classify
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: classify-watch 逐项容错且批量末尾才刷atlas
verify: classify.py cmd_watch_sync_classify 含小结与 refresh_atlas=False
applies: pmem-atlas / classify-watch --apply
source:
  kind: conversation
---
大批量 --apply 每张 ingest 都 refresh_atlas 易中途崩（partial）。
更正：单张 try/except 跳过；
ingest(refresh_atlas=False)；
整批结束后刷一次 atlas；
小结可续跑。
