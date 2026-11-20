---
id: 01M7WSRELEASE015ART
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M7WHTJGJ8KSN67BPFP2EYMJY
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py
- improve/memory_trust.py
- feedback.py#_write_memory_entry_unlocked
revision: git:b2791b0
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 当前用户包版本是 v0.16.15-art（记忆trust + doctor/B2 加固）
scope: project
verify: rg "VERSION =" pmem_art.py；pyw -3 -u scripts/pack_pmem_art.py 后 dist/pmem-art-0.16.15-art.zip
applies: 向画师发放用户包或写版本说明时
aliases:
- 0.16.15-art
- v0.16.15-art
- memory trust release
source:
  conversation: deep-check-release-20261120
---
现象：0.16.14-art 之后合入记忆可信度（candidate→verified→canonical）、doctor 扩展、B2 assemble、finish 同资产不降级 trust、layer-split 执行卡裁包与展陈闸对齐 3 轮。
结论：对外发放与 README/USER_MANUAL/skills-homepage 对齐的当前用户包版本为 **v0.16.15-art**。
打用户 zip：`pyw -3 -u scripts/pack_pmem_art.py`，产物 `dist/pmem-art-0.16.15-art.zip`；
GitHub Release 标签 `v0.16.15-art`。
证据：`pmem_art.py` VERSION=`0.16.15-art`；`memory promote|revoke|resolve` CLI；docs/MEMORY_TRUST.md · BENCHMARK_LAYERS.md · SCORING_CANON.md。
影响：画师装包与文档版本号以此为准；自动写入记忆仍为 candidate，主美确认后再升。
