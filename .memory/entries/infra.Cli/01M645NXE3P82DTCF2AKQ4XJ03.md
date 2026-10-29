---
id: 01M645NXE3P82DTCF2AKQ4XJ03
module: infra.Cli
entity: Packaging
kind: correction
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py
- .memory/config.yaml
- .cursor/mcp.json
revision: git:034a503
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: GitHub开发仓必须带pmem，只有用户zip去掉
scope: project
verify: git ls-files .memory/config.yaml 有输出；python -m unittest tests.test_pack_pmem_art
  -v 的 zip 仍无 .memory
applies: 本仓库同时挂 pmem 与 pmem-art 期间
aliases:
- 仓库带pmem
- zip不带pmem
verified: '2026-10-30'
verified_at: '2026-10-30T01:52:48.704+08:00'
---
用户澄清：GitHub 开发仓必须带 pmem 脚手架（.memory、pmem hook、pmem MCP、pmem.mdc、AGENTS/CLAUDE 的 pmem 段）。
只有给美术用户的 zip 包去掉这些。
上一轮提交 034a503 把 pmem 留在工作区、没推进 GitHub，是理解反了。
zip 仍由 scripts/pack_pmem_art.py 排除 .memory 和 pmem hook，不要改成连仓库也不带 pmem。
