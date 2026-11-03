---
id: 01M6H141PCEHFE8ABAPP6VTBDF
module: infra.Cli
entity: AtlasWorkbench
kind: exclusion
status: active
supersedes: []
anchors:
- build_atlas.py#connectOrOfferWorkbenchLauncher
revision: git:91abe1f
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 禁止指望双击 HTML 自动起 Python，改用打开工作台脚本
verify: file:// 页无法自行起本机进程；重试连通会下载启动脚本
applies: art-atlas 用 file:// 打开时
aliases:
- 双击html自动启动
- file自动起服务
---
排除：期望双击 art-atlas.html（file://）时由网页 JS 自动启动本机 python/atlas_reveal。浏览器安全策略不允许 file:// 或普通网页 spawn 本机进程，这条路做不到。
正确替代：1) 双击项目根「打开工作台.cmd」；2) 在已打开的 HTML 点「重试连通」下载启动脚本再双击；3) 终端跑 python pmem_art.py atlas 后用打印的 http 地址。
与「文件夹按钮禁止回退成浏览器打开 file 目录」是不同边界，互不替代。
