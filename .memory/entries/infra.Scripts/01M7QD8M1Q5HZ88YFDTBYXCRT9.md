---
id: 01M7QD8M1Q5HZ88YFDTBYXCRT9
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M7Q5HGCFK4YA6VFAT0EECDHH
anchors:
- scripts/pack_pmem_art.py
- pmem_art.py
- README.md
revision: git:2936630
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 用户包已升到 v0.16.13-art，取代 0.16.12
verify: gh release view v0.16.13-art；zip 名 pmem-art-0.16.13-art.zip；VERSION==0.16.13-art；unittest
  tests.test_pack_pmem_art
applies: 画师下载用户包 / Release 分发
aliases:
- 0.16.13-art
- 用户包
- release
source:
  conversation: 1c3c3fc0-ee1e-4b91-82b0-59a517862363
---
用户包已升到 v0.16.13-art（https://github.com/mry-ship/pmem-art/releases/tag/v0.16.13-art）。
zip 文件名是 pmem-art-0.16.13-art.zip。
0.16.12-art 仍可下载但不作为最新推荐。
本版：新增 draw.touchup 局部改快通道；口语映射与 converge 自动 low/max_rounds≤2/跳过正式合理性闸；禁止掉进普通图三轮。
GitHub 开发仓仍带 pmem 脚手架；仅用户 zip 去掉 .memory / .memory-art / pmem hook / AGENTS·CLAUDE 的 pmem:begin。
