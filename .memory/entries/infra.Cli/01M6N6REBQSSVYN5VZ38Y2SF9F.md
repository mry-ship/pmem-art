---
id: 01M6N6REBQSSVYN5VZ38Y2SF9F
module: infra.Cli
entity: CursorHooks
kind: feature
status: active
supersedes:
- 01M6KVMT0PR0B62X2V1E7FN63R
anchors:
- lifecycle.py#ensure_cursor_stubs
- lifecycle.py#_is_pmem_rd_hook_command
- .cursor/hooks.json
revision: git:e5571b3
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: Windows art hooks 用 pyw；ensure_cursor_stubs 合并保留 pmemw
verify: python -m unittest tests.test_cursor_hooks_stubs -q；.cursor/hooks.json 含 pyw
  -3 -u pmem_art.py 且含 pmemw
applies: Windows Cursor 装 pmem-art；本仓库另挂 pmem 时
verified: '2026-11-11'
verified_at: '2026-11-11T01:15:57.631+08:00'
---
需求来源：GenerateImage 前后黑框狂闪。必须保持：
  1) .cursor/hooks.json 与 .codex/hooks.json 的 pmem_art pre-gen/post-asset/stop 在 Windows 用 pyw -3 -u，禁止 python3/||/ .cmd。
  2) ensure_cursor_stubs 刷新时合并保留 pmemw/pmem/.memory/bin/pmem-hook；
并把已有 python3 art 启动器改写成当前平台前缀。
  3) stop 必须保留（闭环 followup）。
适用条件：Windows Cursor 本仓（同时挂 pmem）与用户包。
入口：lifecycle.py#ensure_cursor_stubs；
.cursor/hooks.json。
