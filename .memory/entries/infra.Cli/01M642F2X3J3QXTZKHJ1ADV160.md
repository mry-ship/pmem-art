---
id: 01M642F2X3J3QXTZKHJ1ADV160
module: infra.Cli
entity: DualMemory
kind: decision
status: active
supersedes: []
anchors:
- .cursor/mcp.json
- .memory/config.yaml
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 研发记忆用 .memory，美术记忆用 .memory-art，两套 MCP 不混
scope: project
verify: pmem doctor 通过且 .cursor/mcp.json 同时有 pmem 与 pmem-art
aliases:
- pmem-art
- 双记忆
---
本仓库同时挂两套记忆，职责不能混。
pmem（mry-ship/pmem）管研发结论：改代码前查、改完记，目录是 .memory/，MCP 工具是 search_memory / record_memory。
pmem-art 管美术口味、配方、闭环生图，目录是 .memory-art/，MCP 是 pmem-art。
改 Python/技能路由查 pmem；
生图、风格、红线走 pmem-art。
不要把美术 recipe 写进 .memory/entries，也不要用 pmem-art 存代码根因。
