---
id: 01M64FGB5TBH9T7XNG2GE31P59
module: infra.Cli
entity: RouteCmd
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: CLI route：本地分流建议与--rebuild同步话术库
verify: python3 pmem_art.py route --text "画一张水彩半身"；python3 pmem_art.py route --rebuild
applies: 本仓库与用户安装后的 pmem-art CLI
aliases:
- route命令
source:
  conversation: cb47efd7-68ce-4970-9af1-8ef2b26869b1
---
需求来源：总控强制先调本地路由。
必须保持：pmem_art.py route --text 打印 banner/plan/近邻；
--json 机读；
--rebuild 重建打包库并 sync 到项目 .memory-art/route_bank/；
不 import pmem 包；
不把美术 recipe 写入 .memory。
入口：python3 pmem_art.py route …；skills --install 也会 sync。
