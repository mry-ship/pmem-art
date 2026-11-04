---
id: 01M6M0864KAAP2VMVQS87P9Q3A
module: infra.Cli
entity: McpRoot
kind: correction
status: active
supersedes:
- 01M6KW2XH30KW3YS8BX2N7G5M8
anchors:
- .cursor/mcp.json
- /Users/yanghu/.cursor/mcp.json
- /Users/yanghu/.local/bin/pmem-mcp-workspace
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: macOS Cursor MCP：pmem 须绝对路径+PATH；用户级用 workspace 启动器
scope: project
verify: GetDynamicTools 能见 project-0-pmem-art-pmem；list_modules 的 project_root 为本仓；~/.cursor/mcp.json
  的 pmem.command 为 pmem-mcp-workspace
applies: macOS 上 Cursor（Dock/GUI 启动）接入 pmem MCP 时
aliases:
- MCP不能用
- pmem MCP
- Connection closed
- PATH
source:
  conversation: 5b2e22e0-bbdc-47df-9cc5-9a97a8252cc5
---
现象：删掉用户级 pmem 后，本对话动态工具无 pmem；
项目 .cursor/mcp.json 虽有 pmem，但 Cursor GUI PATH 仅 /usr/bin:/bin:/usr/sbin:/sbin，裸命令 pmem 找不到；
项目 MCP 常停在 disconnected/需审批。
原因：Dock 启动的 Cursor 不带 ~/.local/bin；仅靠项目级配置不够稳。
取舍：
  1) 项目 .cursor/mcp.json 的 pmem/pmem-art 改为绝对路径命令并带 PATH/PYTHONUNBUFFERED；
  2) 用户级 ~/.cursor/mcp.json 恢复 pmem，command=/Users/yanghu/.local/bin/pmem-mcp-workspace，args=${workspaceFolder}，禁止写死别的项目 root。
证据：修复后 project-0-pmem-art-pmem 与 user-pmem 均为 ready；list_modules 返回 project_root=/Users/yanghu/Desktop/pmem-art。
排除：继续用户级写死量化-股票-数字币 root；项目级只写裸 pmem 不带 PATH。
