---
id: 01M6RF4A3029ZCBRNYY0FNBQ9W
module: infra.Scripts
entity: PackUserZip
kind: feature
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py#should_skip
- tests/test_pack_pmem_art.py
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 用户包不打包 art-atlas.html，无瑕度只查 build_atlas.py
verify: python -m unittest tests.test_pack_pmem_art -v
applies: 给美术用户分发 pmem-art 时
aliases:
- art-atlas.html
- 画廊
- 用户包
- pack
source:
  conversation: d0bd94be-2445-43db-99f2-fed53b9d8564
---
需求来源：画廊 HTML 是各项目 atlas 现生成的，仓库 gitignore。干净树没有它，本机生成过又会把本仓画廊打进用户包。
必须保持：scripts/pack_pmem_art.py 的 should_skip 跳过任何名为 art-atlas.html 的文件；
tests/test_pack_pmem_art 断言 zip 内没有该文件。
第六维标签「无瑕度」仍以 zip 内 build_atlas.py 的 flawlessness 文案为准。
安装后由 pmem_art.py atlas 现生成工作台。
适用条件：给美术用户打 zip 时。
入口：python scripts/pack_pmem_art.py。
