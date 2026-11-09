---
id: 01M707MTKPCGZQ9KEP8V72XKF5
module: infra.Cli
entity: LoadProject
kind: feature
status: active
supersedes: []
anchors:
- pmem_art.py#load_project
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: load_project 容忍异机 Windows 绝对资产路径
verify: 带异机 Windows 路径条目时 python3 pmem_art.py search --module brand.WorldStyle 能出
  JSON
applies: load_project 扫描条目 assets 是否存在时
---
需求：条目 assets.path 若为异机 Windows 绝对路径或超长名，macOS 上 root/join+is_file 会 OSError Errno 63，导致 search/converge start 整段崩。
必须保持：缺失资产仍记入 asset_gap，不因探测失败中断 load_project。
适用：load_project 扫描条目 assets 是否存在时。
入口：pmem_art.py load_project 内 _asset_file_present（盘符路径/UNC/超长/OSError 一律当缺失）。
