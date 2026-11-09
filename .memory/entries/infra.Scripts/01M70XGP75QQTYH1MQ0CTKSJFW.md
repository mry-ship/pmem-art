---
id: 01M70XGP75QQTYH1MQ0CTKSJFW
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py
- pmem_art.py
- README.md
- USER_MANUAL.md
revision: git:6355311
author: yanghu
note_date: '2026-11-10'
summary: 用户包已升到 v0.16.7-art，取代 0.16.6
verify: gh release view v0.16.7-art；zip 名 pmem-art-0.16.7-art.zip
applies: 画师下载用户包 / Release 分发
aliases:
- 0.16.7-art
- 用户包
---
用户包已升到 v0.16.7-art（https://github.com/mry-ship/pmem-art/releases/tag/v0.16.7-art）。
zip 文件名是 pmem-art-0.16.7-art.zip。
0.16.6-art 仍可下载但不作为最新推荐。
本版含风格优先级、4 轮闭环、路由 false-fire 与 SkillsKit 分层。
