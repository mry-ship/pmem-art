---
id: 01M6K4P6MB41R1M5HK370WFPDM
module: infra.Cli
entity: CursorHooks
kind: feature
status: active
supersedes: []
anchors:
- lifecycle.py#ensure_cursor_stubs
- .cursor/hooks.json
revision: git:6af8aef
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: Cursor hooks：GenerateImage pre/post + stop(pyw)
verify: python -m unittest tests.test_cursor_hooks_stubs tests.test_converge_loop
  -q
applies: Cursor 项目装 pmem-art 后跑生图闭环
---
需求来源：用户包在其他项目出图后对话不自动续审。
必须保持：
1) ensure_cursor_stubs / .cursor/hooks.json：preToolUse+postToolUse 仅 matcher=GenerateImage；stop 必有且 loop_limit=8。
2) Windows 命令前缀 pyw -3 -u；非 Windows 用 python3；禁止 || 与 .cmd。
3) stop 按 conversation_id 归属发 followup（既有 StopFollowupScope）。
适用条件：pmem_art.py init / doctor 刷新 stubs；用户 zip 解压后的 Cursor 项目。
入口：lifecycle.py#ensure_cursor_stubs；pmem_art.py hook stop。
