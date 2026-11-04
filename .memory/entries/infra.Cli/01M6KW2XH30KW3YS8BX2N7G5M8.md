---
id: 01M6KW2XH30KW3YS8BX2N7G5M8
module: infra.Cli
entity: McpRoot
kind: decision
status: active
supersedes: []
anchors:
- .cursor/mcp.json
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 多项目时清空用户级 pmem，只用各项目 .cursor/mcp.json
scope: project
verify: pmem doctor 不再提示用户级也注册了 pmem；本仓 .cursor/mcp.json 含 pmem；~/.cursor/mcp.json
  无 pmem 键
applies: 本机多项目同时用 Cursor + pmem 时
aliases:
- 用户级mcp
---
现象：~/.cursor/mcp.json 注册 pmem 且 --root 写死「量化-股票-数字币」，doctor 警告可能盖住本仓项目配置。
取舍：删掉用户级 pmem，保留 unityMCP/playwright/XcodeBuildMCP；
pmem-art、量化-股票-数字币、UI-image 均已有项目级 .cursor/mcp.json（--root ${workspaceFolder}）。
备份：~/.cursor/mcp.json.bak-remove-pmem-20261105-021028。
生效：需重载 Cursor MCP / 重开窗口后本仓才稳定连到项目级 pmem。
