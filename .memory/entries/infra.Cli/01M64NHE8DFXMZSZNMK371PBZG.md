---
id: 01M64NHE8DFXMZSZNMK371PBZG
module: infra.Cli
entity: AtlasAllImages
kind: feature
status: active
supersedes:
- 01M64NAYGA42JFCKQ12CW758AT
anchors:
- build_atlas.py
- atlas_index.py#reveal_in_os
- pmem_art.py
- tests/test_atlas_all_images.py
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 工作台右键菜单：另存为/复制/访达定位选中图片
verify: python3 -m unittest tests.test_atlas_all_images -v；HTML 含 revealInFolder/showImgCtxMenu；pmem_art.py
  reveal 能 open -R
applies: 使用 art-atlas 工作台找图定位时
aliases:
- 访达
- 文件夹
- 另存为
- 右键菜单
- reveal
source:
  conversation: 7e5e2160-95b3-4c29-934e-6fa0f52ed769
---
需求来源：美术要在工作台点一下就能跳到系统访达/资源管理器并定位到该图，不只是编辑器打开。
必须保持：缩略图与灯箱支持右键菜单（复制绝对/相对/文件名、另存为、在文件夹中显示、编辑器打开、放大查看）；
📁 按钮与灯箱「文件夹」调用 revealInFolder；
浏览器若拦 file:// 则下载「打开图片位置」脚本（macOS open -R / Windows explorer /select）；
命令行 python3 pmem_art.py reveal <path> 直接系统定位。
适用条件：art-atlas 工作台与 reveal CLI。
入口：双击 art-atlas.html 右键图片；或 pmem_art.py reveal。
