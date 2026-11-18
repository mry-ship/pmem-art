---
id: 01M7Q5HGCFK4YA6VFAT0EECDHH
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M7N06C7SQHD3G1GY4GCA7MMV
anchors:
- scripts/pack_pmem_art.py
- pmem_art.py
- README.md
revision: git:405e86a
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 用户包已升到 v0.16.12-art，取代 0.16.11
verify: gh release view v0.16.12-art；zip 名 pmem-art-0.16.12-art.zip；VERSION==0.16.12-art；unittest
  tests.test_pack_pmem_art
applies: 画师下载用户包 / Release 分发
aliases:
- 0.16.12-art
- 用户包
- release
source:
  conversation: a6ab8906-310c-42d9-a9c3-a97c62f08828
---
用户包已升到 v0.16.12-art（https://github.com/mry-ship/pmem-art/releases/tag/v0.16.12-art）。
zip 文件名是 pmem-art-0.16.12-art.zip。
0.16.11-art 仍可下载但不作为最新推荐。
本版：出图 pack_headings 并入「交件可见」；emit-prompt/judge 明确垫图策略；finish settle 后写 assets/.../final.*。
GitHub 开发仓仍带 pmem 脚手架；仅用户 zip 去掉 .memory / pmem hook / AGENTS·CLAUDE 的 pmem:begin。
