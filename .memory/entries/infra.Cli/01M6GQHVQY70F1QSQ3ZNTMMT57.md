---
id: 01M6GQHVQY70F1QSQ3ZNTMMT57
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes: []
anchors:
- build_atlas.py
- atlas_reveal.py
- pmem_art.py
- tests/test_atlas_all_images.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 工作台：提示词履历、批量删除、本地文件夹定位
verify: python -m unittest tests.test_atlas_all_images -v
applies: 使用 art-atlas 工作台时
aliases:
- 批量删除
- 提示词履历
- 文件夹定位
---
需求来源：美术要在详情里看一轮轮提示词怎么改过来的；要相册式批量删除；点文件夹要打开本机资源管理器并选中该图，不要跳浏览器网页目录。
必须保持：详情侧栏展示 converge 提示词优化履历；
工具栏批量删除支持勾选/Ctrl+A/Shift片选/取消/真删；
悬停图 Delete 可删；
文件夹只走 reveal 桥或下载定位脚本，禁止 window.open 网页目录；
reveal 服务标识 pmem-atlas-reveal，默认端口 27865，支持 /api/delete。
适用条件：使用 art-atlas 工作台时。
入口：art-atlas.html；python pmem_art.py atlas；atlas_reveal.py。
