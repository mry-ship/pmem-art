---
id: 01M739M1XAQ7GK8YMPJFZ9BBJW
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M735PAANC63JF3JZ2BH921BW
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py
- README.md
revision: git:e47ed01
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 用户包已升到 v0.16.9-art，取代 0.16.8
verify: gh release view v0.16.9-art；zip 名 pmem-art-0.16.9-art.zip；VERSION==0.16.9-art
applies: 画师下载用户包 / Release 分发
aliases:
- 0.16.9-art
- 用户包
- release
source:
  conversation: 813b285a-1cff-4227-bdd6-587c9e0528e2
---
用户包已升到 v0.16.9-art（https://github.com/mry-ship/pmem-art/releases/tag/v0.16.9-art）。
zip 文件名是 pmem-art-0.16.9-art.zip。
0.16.8-art 仍可下载但不作为最新推荐。
本版：模块覆盖率 100%；非图 sidecar 不进图片 QA；ConvergeGate 合并与记忆收口；atlas hygiene / classify-watch 归位。
健康门连续两轮 CLEAN。
