---
id: 01M64KPMJERH4XKZ4926ACXKK6
module: infra.Cli
entity: AtlasAllImages
kind: feature
status: active
supersedes: []
anchors:
- atlas_index.py
- build_atlas.py#generate_atlas_html
- pmem_art.py#load_project
- tests/test_atlas_all_images.py
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: Atlas所有图：可见索引+虚拟窗口懒解码+缩略图96–360滑杆
verify: python3 -m unittest tests.test_atlas_all_images -v；HTML 含 paintVirtualGallery
  / THUMB_MIN=96 / MAX_DECODE=8
applies: 生成或 silent refresh art-atlas 工作台时
aliases:
- 所有图
- art-atlas
- 可见索引
source:
  conversation: 9e754f53-f1c2-471a-b7eb-2375d055ae75
---
需求：美术双击 art-atlas 就能看到项目里今天出的图（含 Cursor 散图），按时间/类型筛，灯箱放大并定位；低频 Tab 收进「更多」；滚动必须丝滑，缩略图可调一屏密度。
实现：atlas_index 扫描可见索引不 formal ingest；
默认无 data_uri；
画廊用虚拟窗口只挂视口附近 DOM；
图片解码并发上限 8；
缩略图滑杆 96–360（默认 180，＜140 进紧凑模式藏正文）；
搜索 140ms 防抖；
ping 热更新 atlas_data.json。
必须保持：可见≠正式 ingest；默认不嵌 base64（仅 --embed）；默认所有图→今天；缩略图有上下限防过小/过大。
入口：python3 pmem_art.py atlas；双击 art-atlas.html。
