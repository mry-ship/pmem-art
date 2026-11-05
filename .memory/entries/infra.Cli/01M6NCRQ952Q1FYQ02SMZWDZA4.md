---
id: 01M6NCRQ952Q1FYQ02SMZWDZA4
module: infra.Cli
entity: CursorHooks
kind: feature
status: active
supersedes: []
anchors:
- lifecycle.py#_strip_shell_from_pmem_pretool
revision: git:9d79f57
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: Windows pmem pre-tool 只留 MCP 防写md闪窗
verify: python -m unittest tests.test_cursor_hooks_stubs -q
applies: Windows；Cursor-Pmem-Art 双挂 pmem
---
需求来源：双挂 pmem 的 Art 仓用 Write 写 md 仍弹控制台。
必须保持：ensure_cursor_stubs 刷新时，win32 上 pmemw/pmem pre-tool matcher 去掉 Write|StrReplace|Edit|MultiEdit|EditNotebook|Delete|Shell|Bash，只留 MCP|record_memory|search_memory；
非 Windows 不变；
art GenerateImage/Shell/stop 钩子仍保留。
适用：Windows + 本仓库同时接 pmem。
入口：lifecycle.ensure_cursor_stubs → _strip_shell_from_pmem_pretool。
