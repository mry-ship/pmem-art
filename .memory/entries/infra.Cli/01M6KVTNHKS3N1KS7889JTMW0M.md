---
id: 01M6KVTNHKS3N1KS7889JTMW0M
module: infra.Cli
entity: CursorHooks
kind: correction
status: active
supersedes:
- 01M6KVMJ3J9NPEXG7YC92DAAJB
anchors:
- lifecycle.py#_is_pmem_rd_hook_command
- .cursor/hooks.json
- .cursor/mcp.json
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 升级后 Hook 官方入口是 pmemw；MCP 仍用 pmem
scope: project
verify: command -v pmemw；.cursor/hooks.json 含 pmemw hook；.cursor/mcp.json 的 pmem.command
  为 pmem；pmem doctor Hooks 已接入
applies: 已安装含 pmemw 入口的当前版 pmem 后
aliases:
- pmemw
---
旧排除「禁止用 pmemw 接 Cursor hooks」只在本机 PATH 没有 pmemw、闸门因此失效时成立。
当前已装到 GitHub master（commit 4d776a54c5ff，版本号仍标 0.6.1）：提供 pmemw 入口；pmem init / doctor 认 pmemw hook；Windows 用它少弹控制台。
MCP 仍必须 command=pmem（禁止 pmemw），避免 stdio 被掐断。
本仓库 ensure_cursor_stubs 刷新时须合并保留 pmemw hook / pmem hook / .memory/bin/pmem-hook。
