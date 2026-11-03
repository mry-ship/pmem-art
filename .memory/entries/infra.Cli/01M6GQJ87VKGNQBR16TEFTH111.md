---
id: 01M6GQJ87VKGNQBR16TEFTH111
module: infra.Cli
entity: AtlasWorkbench
kind: exclusion
status: active
supersedes: []
anchors:
- build_atlas.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 文件夹按钮禁止回退成浏览器打开file目录
applies: art-atlas 点文件夹时
aliases:
- 文件夹网页回退
---
排除：reveal 失败时用 window.open(file://文件夹) 当回退。那会变成网页目录浏览，不是资源管理器选中文件。应只走 localhost reveal 或下载打开图片位置脚本。
