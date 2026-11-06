---
id: 01M6QY7V8ESGC9XV2NBWKD6JTR
module: infra.Cli
entity: Install
kind: feature
status: active
supersedes:
- 01M6KVTQ3NXN2NB5YWDAJ4009E
anchors:
- .cursor/hooks.json
- .memory/bin/pmem-hook
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 本机 pmem 已升到 0.6.2（本地仓 2bec8eb）
verify: pmem --version 打印 0.6.2；pmemw --version 可用；pmem doctor 不再报缺 pmemw
applies: 本机用 uv tool 安装的 pmem 升级时
---
需求来源：用户要求 uv tool upgrade pmem 并升级本项目接入。
必须保持：有 pmem serve 占用 .local/bin/pmem.exe 时，禁止 uv tool install --force；
先 uv tool upgrade（可失败于入口复制），再对工具环境就地 uv pip install --pyw -3 -u %APPDATA%/uv/tools/pmem/Scripts/python.exe --upgrade "pmem[embed] @ <源>"；
缺 pmemw 时从同目录 Scripts 手工拷到 ~/.local/bin。
升级后必须在项目根 pmem init --agents auto --hooks auto。
当前：源为本地 Cursor-Project-Memory commit 2bec8eb，命令版号 0.6.2，已有 pmemw；项目 hooks/mcp/mdc 已刷新。
入口：uv tools 环境 + 项目 pmem init。
