---
id: 01M64NRNYJQPZVQT00RTD4WF2S
module: infra.Cli
entity: AtlasAllImages
kind: feature
status: active
supersedes:
- 01M64NHE8DFXMZSZNMK371PBZG
anchors:
- atlas_index.py#classify_plate
- build_atlas.py
- tests/test_atlas_all_images.py
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 叠层看原图+reveal访达；列表用_thumbs小图加速滑动
verify: tests.test_atlas_all_images：openViewer/revealViaBridge/thumbSrc/test_gallery_thumbs_created_for_large_images
applies: art-atlas 工作台看图与定位
aliases:
- 定稿
- 过程稿
- plate
source:
  conversation: 7e5e2160-95b3-4c29-934e-6fa0f52ed769
---
需求来源：文件夹/点图放大；以及窗口刷新与滑动后出图很慢。
必须保持：
1) 点缩略图 openViewer 半透明叠层放大原图，点空白/Esc 关闭；
2) 右键含在文件夹中显示/复制路径；📁 经 localhost atlas_reveal /api/reveal 调 open -R；
3) 画廊卡片用 thumbSrc（.memory-art/_thumbs JPEG≤360），点开仍看原图；虚拟窗口直出 src，VIRT_ROW_BUFFER=6。
适用：art-atlas 工作台。
入口：python3 pmem_art.py atlas 后打开 art-atlas.html。
