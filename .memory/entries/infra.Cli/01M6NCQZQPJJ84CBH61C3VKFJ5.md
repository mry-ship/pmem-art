---
id: 01M6NCQZQPJJ84CBH61C3VKFJ5
module: infra.Cli
entity: WindowsConsole
kind: conclusion
status: active
supersedes: []
anchors:
- lifecycle.py#_strip_shell_from_pmem_pretool
- .cursor/hooks.json
revision: git:9d79f57
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 写md弹窗：pmem pre-tool 去掉Write
verify: ensure_cursor_stubs 后 hooks.json 的 pmemw pre-tool matcher 无 Write；unittest
  tests.test_cursor_hooks_stubs -q
applies: Windows + Cursor-Pmem-Art 双挂 pmem 写文档
---
现象：pmem-art 用 Write 写 md/技能文档也会弹控制台。
根因：双挂 pmem 时 pre-tool matcher 仍含 Write|Edit；
Cursor Windows 经 PowerShell 转发每个 Hook 必弹，与 pmemw 无关；
config 虽 ignore **/*.md，进程仍会起。
处理：lifecycle._strip_shell_from_pmem_pretool 在 win32 同时去掉 Write|StrReplace|Edit|MultiEdit|EditNotebook|Delete|Shell|Bash，只留 MCP|record_memory|search_memory。
代价：改 .py 时闸门不再拦 Write，靠规则与 afterMCP。
须重开 Art 的 Cursor 窗口。
