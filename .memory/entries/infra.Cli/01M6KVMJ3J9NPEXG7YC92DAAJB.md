---
id: 01M6KVMJ3J9NPEXG7YC92DAAJB
module: infra.Cli
entity: CursorHooks
kind: exclusion
status: active
supersedes: []
anchors:
- .cursor/hooks.json
- .memory/bin/pmem-hook.cmd
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 禁止用 pmemw 接 Cursor hooks，本机无命令闸门失效
scope: project
verify: command -v pmemw 失败；.cursor/hooks.json 无 pmemw；pmem doctor Hooks 已接入
applies: 本机 PATH 只有 pmem 没有 pmemw 时
aliases:
- pmemw hook
---
现象：pmem doctor 报 Hooks 未接入（闸门不生效）；.cursor/hooks.json 写 pmemw hook，PATH 无 pmemw。
排除：继续用 pmemw / 只靠 doctor 字符串碰巧匹配。
正确：官方入口是 pmem hook 与 .memory/bin/pmem-hook；Windows 无黑框需求由 pyw 服务 pmem-art，不代替 pmem 命令名。
