---
id: 01M80RELEASE017ART
module: infra.Scripts
entity: Packaging
kind: correction
status: archived
supersedes:
- 01M7XAHX2QGQH697ZN65QZJ06K
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py
- improve/memory_trust.py
- docs/MEMORY_TRUST.md
revision: local:0.16.17-art
author: cursor-agent
note_date: '2026-11-23'
summary: 当前用户包版本是 v0.16.17-art（trust 文档与迁移入口）
scope: project
verify: rg "VERSION =" pmem_art.py；python3 scripts/pack_pmem_art.py 后 dist/pmem-art-0.16.17-art.zip
  不含 .memory
applies: 向画师发放用户包或写版本说明时
aliases:
- 0.16.17-art
- v0.16.17-art
---
现象：0.16.16-art 之后补齐 MEMORY_TRUST 与代码一致、memory audit/promote-missing、doctor 缺 trust 软信号、四格 keep 不再灌 L1 locks。
结论：对外发放与 README/USER_MANUAL/skills-homepage 对齐的当前用户包版本为 v0.16.17-art。
打用户 zip：python3 scripts/pack_pmem_art.py，产物 dist/pmem-art-0.16.17-art.zip；
zip 不含 .memory 与 pmem hook。
GitHub Release 标签 v0.16.17-art。
证据：pmem_art.py VERSION=0.16.17-art。
