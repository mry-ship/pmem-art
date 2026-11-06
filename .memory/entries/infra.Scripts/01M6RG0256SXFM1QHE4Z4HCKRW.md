---
id: 01M6RG0256SXFM1QHE4Z4HCKRW
module: infra.Scripts
entity: PackUserZip
kind: feature
status: active
supersedes:
- 01M6RF4A3029ZCBRNYY0FNBQ9W
anchors:
- scripts/pack_pmem_art.py#should_skip
- tests/test_pack_pmem_art.py
revision: git:2b4b04f
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 用户包不带画廊、工作树和根目录探针
verify: python -m unittest tests.test_pack_pmem_art -v
applies: 给美术用户分发 pmem-art 时
aliases:
- art-atlas.html
- worktrees
- 用户包
source:
  conversation: d0bd94be-2445-43db-99f2-fed53b9d8564
---
需求来源：画廊 HTML 是各项目 atlas 现生成的；Claude 工作树是整仓副本；仓库根上划线开头的是本地探针。这三类都不能进用户包。
必须保持：scripts/pack_pmem_art.py 的 should_skip 跳过 art-atlas.html、路径中的 worktrees、以及仓库根上以划线开头的文件。
tests/test_pack_pmem_art 断言 zip 内没有这些。
第六维「无瑕度」仍只查 build_atlas.py。
安装后由 pmem_art.py atlas 现生成工作台。
适用条件：给美术用户打 zip 时。
入口：python scripts/pack_pmem_art.py。
