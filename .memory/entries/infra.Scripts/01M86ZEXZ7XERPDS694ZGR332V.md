---
id: 01M86ZEXZ7XERPDS694ZGR332V
module: infra.Scripts
entity: PackUserZip
kind: feature
status: active
supersedes:
- 01M645KA9K6MMEZJB2JBAGTQEB
anchors:
- scripts/pack_pmem_art.py#iter_source_files
- scripts/pack_pmem_art.py#assert_pack_clean
revision: git:b0d33b0
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 用户包只收已跟踪文件，并且必须去掉.memory和pmem hook
scope: project
verify: python -m unittest tests.test_pack_pmem_art -v
applies: 给美术用户分发 pmem-art 时
aliases:
- 用户包
- pack_pmem_art
source:
  conversation: ba9d4a3d-e1c3-47a2-8066-198c30709ef1
---
需求来源：画师用户包不要带研发用 pmem 记忆系统。
必须保持：scripts/pack_pmem_art.py 只收 git 已跟踪文件，再去掉 .memory、pmem hook、pmem MCP，以及 AGENTS.md / CLAUDE.md 里的 pmem 段。
开发仓继续保留 .memory，不要为了用户包干净而从 GitHub 仓库删掉 pmem。
适用：打 GitHub Release 用户 zip 时。
入口：pyw -3 -u scripts/pack_pmem_art.py，产物 dist/pmem-art-<VERSION>.zip。
