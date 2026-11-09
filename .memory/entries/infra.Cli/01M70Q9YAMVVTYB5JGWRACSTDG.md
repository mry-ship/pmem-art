---
id: 01M70Q9YAMVVTYB5JGWRACSTDG
module: infra.Cli
entity: AtlasWriteLock
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py#write_atlas_html
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: write_atlas_html 跨进程文件锁与原子替换
verify: python3 -m unittest tests.test_atlas_write_lock -q
applies: python3 pmem_art.py atlas 或 converge finish 刷 atlas 时
---
必须保持：并发 atlas 刷新用 flock（POSIX）/ msvcrt（Windows）；
先写临时文件再 replace；
CLI atlas 子命令走 write_atlas_html，与 finish 后台刷同一入口。
需求来源：finish/atlas 并发卡死与半写。
入口：pmem_art.write_atlas_html；
python3 pmem_art.py atlas。
