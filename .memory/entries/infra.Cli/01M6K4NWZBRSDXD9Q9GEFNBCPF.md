---
id: 01M6K4NWZBRSDXD9Q9GEFNBCPF
module: infra.Cli
entity: CursorHooks
kind: exclusion
status: active
supersedes: []
anchors:
- lifecycle.py#ensure_cursor_stubs
- lifecycle.py#_hook_python_prefix
- .cursor/hooks.json
revision: git:6af8aef
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 消黑框禁止删 stop hook，改用 pyw
scope: project
verify: python -m unittest tests.test_cursor_hooks_stubs -q；.cursor/hooks.json 含 stop
  且无 ||
applies: Windows Cursor 装 pmem-art 用户包后出图闭环
aliases:
- 图不进控制台
- stop followup 丢失
verified: '2026-11-05'
verified_at: '2026-11-05T02:02:33.280+08:00'
---
现象：用户包装到别的项目后，GenerateImage 出图了但对话不会自动续跑审图（「图不会自动进控制台」）。
根因：为消 Windows 黑框，把 hooks.json 的 stop 整段删掉；技能依赖 stop 的 followup_message 把闭环拉回对话。
排除：消黑框时删掉 stop；或用会弹框的 || / .cmd 回退链。
正确做法：pre/post 仍只绑 GenerateImage；stop 必须保留；Windows 用 pyw -3 -u（无黑框、系统路径稳）。
