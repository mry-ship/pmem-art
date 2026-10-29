---
id: 01M642X7NN3FYC3YHX3TH2GKQ6
module: infra.Cli
entity: WindowsCli
kind: conclusion
status: seed
supersedes: []
anchors:
- pmem_art.py#_cli_entry
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: Windows CLI要防编码崩溃，技能文档必须和已安装技能一致
verify: pmem --version 与 python pmem_art.py -h 不崩
applies: Windows PowerShell 调用 pmem_art / pmem 时
aliases:
- 乱码
- 崩溃
---
依据提交 e245862。Windows 上 CLI 会因编码/换行崩掉，文档和安装技能数量必须和已安装技能一致。踩过的坑：PowerShell 5 按 GBK 解码管道会乱码，直接看 pmem 输出或 --brief。
