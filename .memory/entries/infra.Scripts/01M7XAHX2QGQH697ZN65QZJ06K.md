---
id: 01M7XAHX2QGQH697ZN65QZJ06K
module: infra.Scripts
entity: Packaging
kind: correction
status: archived
supersedes:
- 01M7WSRELEASE015ART
superseded_by: 01M80RELEASE017ART
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py
- improve/memory_trust.py
- feedback.py#_write_memory_entry_unlocked
revision: git:ea22106
author: yanghu
note_date: '2026-11-21'
summary: 当前用户包版本是 v0.16.16-art（四格合同与记忆防污染）
scope: project
verify: rg "VERSION =" pmem_art.py；python3 scripts/pack_pmem_art.py 后 dist/pmem-art-0.16.16-art.zip
  不含 .memory
applies: 向画师发放用户包或写版本说明时
aliases:
- 0.16.16-art
- v0.16.16-art
---
现象：0.16.15-art 之后，四格合同与标准路由句分开，未确认记忆不再进提示词，防污染规则写入实际执行包。
结论：对外发放与 README/USER_MANUAL/skills-homepage 对齐的当前用户包版本为 v0.16.16-art。
打用户 zip：python3 scripts/pack_pmem_art.py，产物 dist/pmem-art-0.16.16-art.zip；
zip 不含 .memory 与 pmem hook。
GitHub Release 标签 v0.16.16-art。
证据：pmem_art.py VERSION=0.16.16-art。
影响：开发仓继续保留 .memory；只有用户包去掉 pmem。
