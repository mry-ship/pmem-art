---
id: 01M6NFTSTH04CHWV9TMR8R4B3Z
module: infra.Scripts
entity: Packaging
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py
revision: git:8f37a17
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 当前用户包为 GitHub Release v0.16.4-art
verify: gh release view v0.16.4-art；zip 无 .memory
applies: 给美术用户分发 zip，不含研发 pmem
aliases:
- 0.16.4-art
- 用户包
---
画师分发以 https://github.com/mry-ship/pmem-art/releases/tag/v0.16.4-art 的 pmem-art-0.16.4-art.zip 为准；
仍由 scripts/pack_pmem_art.py 打包，不含 .memory / pmem hook / MCP。
含本轮 merge 商业闸与手册对齐。
