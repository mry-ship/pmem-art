---
id: 01M7N06C7SQHD3G1GY4GCA7MMV
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M789TQ390CK660PZM024HA2A
anchors:
- scripts/pack_pmem_art.py
- pmem_art.py
revision: git:fe8a365
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 用户包已升到 v0.16.11-art，取代 0.16.10
verify: gh release view v0.16.11-art；zip 名 pmem-art-0.16.11-art.zip；VERSION==0.16.11-art；unittest
  tests.test_pack_pmem_art
applies: 画师下载用户包 / Release 分发
aliases:
- 0.16.11-art
- 用户包
- release
source:
  conversation: 4a789d41-7c46-4519-b63d-ab0727e3b6f9
---
用户包已升到 v0.16.11-art（https://github.com/mry-ship/pmem-art/releases/tag/v0.16.11-art）。
zip 文件名是 pmem-art-0.16.11-art.zip。
0.16.10-art 仍可下载但不作为最新推荐。
本版：生图硬顶最多3轮；emit-prompt 主链；safe_early_stop/过程板加固；技能树摘掉研发 pmem 技能壳。
GitHub 开发仓仍带 pmem 脚手架；仅用户 zip 去掉 .memory / pmem hook / AGENTS·CLAUDE 的 pmem:begin。
