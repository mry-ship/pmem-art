---
id: 01M645KA9K6MMEZJB2JBAGTQEB
module: infra.Scripts
entity: PackUserZip
kind: feature
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py
revision: git:034a503
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 用户包由pack_pmem_art.py打zip，必须去掉.memory和pmem hook
verify: python -m unittest tests.test_pack_pmem_art -v
applies: 给美术用户分发 pmem-art 时
aliases:
- 用户包
- 不带pmem
- 单独打包
- standalone
---
需求来源：用户要求提交 GitHub 后生成最新 pmem-art 包，且不带 mry-ship/pmem。
必须保持：python scripts/pack_pmem_art.py 打出的 zip 含 pmem_art.py 与 10 条美术技能，不含 .memory/、pmem.mdc、.mcp.json、pmem hook、mcpServers.pmem。
AGENTS.md/CLAUDE.md 的 pmem:begin 段在打包时剥掉。用户解压后走 init + skills --install。
本仓库开发目录仍可同时挂 pmem，不把 pmem 做成运行时依赖。
入口：python scripts/pack_pmem_art.py；GitHub Release v0.13.0-art。
