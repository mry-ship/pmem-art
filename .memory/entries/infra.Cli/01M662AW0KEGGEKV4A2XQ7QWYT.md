---
id: 01M662AW0KEGGEKV4A2XQ7QWYT
module: infra.Cli
entity: AtlasAllImages
kind: feature
status: active
supersedes:
- 01M64NRNYJQPZVQT00RTD4WF2S
anchors:
- build_atlas.py#cardHtml
- build_atlas.py#bindGalleryActions
- build_atlas.py#openViewer
- atlas_reveal.py#reveal_path
- tests/test_atlas_all_images.py
revision: git:959a507
author: 1002378395@qq.com
note_date: '2026-10-30'
summary: 工作台卡片以图为主；点图叠层放大；文件夹按钮事件委托定位
verify: python -m unittest tests.test_atlas_all_images -v
applies: art-atlas 工作台看图与定位
aliases:
- 工作台
- 点图放大
- 目录按钮
- 定稿底色
- 点图没反应
---
需求来源：美术点缩略图不放大、📁不打开目录；卡片文字压图、信息过杂。
必须保持：
1) 点缩略图 openViewer 半透明叠层放大原图，点空白/Esc 关闭；
2) 右键含在文件夹中显示/复制路径；📁经 localhost atlas_reveal /api/reveal 定位文件（Windows explorer /select,）；
3) 画廊卡片用 thumbSrc（.memory-art/_thumbs JPEG≤360），点开仍看原图；虚拟窗口直出 src，VIRT_ROW_BUFFER=6；
4) 卡片图上不叠信息；定稿/类型标签与文件名在图下；定稿底色实色绿 #10b981；不写完整目录路径，只留 📁 跳转；
5) 点击与📁用 data-path 事件委托（bindGalleryActions）。
排除：不要把 JSON.stringify(路径) 塞进双引号 onclick。
onclick="openViewer(${JSON.stringify(a.path)})" 会生成 onclick="openViewer("assets/...")"，属性在第一个引号截断，点图/📁都没反应。
适用：art-atlas 工作台。
入口：python pmem_art.py atlas 后打开 art-atlas.html。
