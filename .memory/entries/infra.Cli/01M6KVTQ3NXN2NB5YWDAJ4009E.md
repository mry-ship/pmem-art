---
id: 01M6KVTQ3NXN2NB5YWDAJ4009E
module: infra.Cli
entity: Install
kind: feature
status: active
supersedes: []
anchors:
- .cursor/hooks.json
- .memory/bin/pmem-hook
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 本机 pmem 跟踪 GitHub master 4d776a5（版本号仍 0.6.1）
verify: pmem --version；python -c 读 direct_url.json commit；pmem doctor Hooks 已接入
applies: 本机用 uv tool 安装的 pmem 升级时
aliases:
- 升级pmem
---
需求来源：用户要求升级到 GitHub 最新 pmem 记忆系统。
必须保持：有其它项目的 pmem serve 占用时，用 uv pip install --python <uv tools pmem python> --upgrade \"pmem[embed] @ git+https://github.com/mry-ship/pmem.git\" 就地升级，禁止 uv tool install --force。
升级后必须 pmem init 刷新 hooks/mdc；macOS 用 --hooks auto(=full)。
当前：commit 4d776a54c5ff3b05527ba7229d594385ccaa3830；命令版号仍打印 0.6.1；已有 pmemw。
入口：uv tools 环境 /Users/yanghu/.local/share/uv/tools/pmem；项目 pmem init。
