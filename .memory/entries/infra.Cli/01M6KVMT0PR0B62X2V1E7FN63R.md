---
id: 01M6KVMT0PR0B62X2V1E7FN63R
module: infra.Cli
entity: CursorHooks
kind: feature
status: active
supersedes:
- 01M6K4P6MB41R1M5HK370WFPDM
anchors:
- lifecycle.py#ensure_cursor_stubs
- .cursor/hooks.json
- tests/test_cursor_hooks_stubs.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: Cursor hooks：art 生图闭环 + 合并保留 pmemw 闸门
verify: python3 -m unittest tests.test_cursor_hooks_stubs -q；pmem doctor 显示 Hooks
  已接入；hooks 含 pmem_art 与 pmemw hook
applies: Cursor 项目装 pmem-art；本仓库另挂 pmem 时
aliases:
- pmemw
---
需求来源：本仓库同时挂 pmem-art 与 pmem；升级到 GitHub master 后 Hook 入口改为 pmemw。
必须保持：
1) ensure_cursor_stubs 写出 GenerateImage pre/post + stop(loop_limit=8)；
   Windows 用 pyw -3 -u，非 Windows 用 python3；
   禁止 || 与 .cmd。
2) 刷新 stubs 时合并保留「pmemw hook*」「pmem hook*」「.memory/bin/pmem-hook*」，禁止整文件覆盖冲掉研发记忆闸门。
3) 本仓库开发态 pmem init --hooks auto（macOS=full）；用户 zip 仍只含 pmem-art Hook。MCP 用 pmem 不用 pmemw。
适用条件：本仓 init/doctor；用户包解压后的 Cursor 项目。
入口：lifecycle.py#ensure_cursor_stubs；pmem init；.cursor/hooks.json。
