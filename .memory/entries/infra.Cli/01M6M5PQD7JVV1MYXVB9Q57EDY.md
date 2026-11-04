---
id: 01M6M5PQD7JVV1MYXVB9Q57EDY
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes: []
anchors:
- atlas_index.py#SKIP_DIR_NAMES
- lifecycle.py#IGNORE_DIR_NAMES
- downloads/README.md
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: downloads/下载目录不进工作台画廊
verify: python -m pytest tests/test_atlas_all_images.py::TestAtlasAllImages::test_scan_skips_trash_and_workbench_guide
  -q；scan 结果无 downloads/ 与 下载/
applies: 使用 art-atlas 工作台且有外网对标下载图时
aliases:
- 下载目录
- downloads不进画廊
source:
  conversation: 8e3ae576-2e1f-44e5-aebc-a9b80861a3a6
---
需求来源：用户发现外网/店面下载的对标图（曾落在 assets/ui/tilematch_refs）会进工作台画廊。
必须保持：项目根 downloads/（及中文名 下载/）专放对标下载图；
atlas_index.SKIP_DIR_NAMES 与 lifecycle.IGNORE_DIR_NAMES 跳过这两名；
不进用户 zip；
gitignore 忽略内容只留 README。
适用：对标截图、禁止垫像素的参考素材。
入口：把下载图放 downloads/…，再 python3 pmem_art.py atlas。
排除：继续把店面截图丢进 assets/ 下被扫进主画廊。
