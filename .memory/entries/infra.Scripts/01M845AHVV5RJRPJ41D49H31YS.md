---
id: 01M845AHVV5RJRPJ41D49H31YS
module: infra.Scripts
entity: LayerSplitFramePaste
kind: feature
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/compose.py#place_band
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆图层把画面带一对一贴进脚印，不把引擎画布 contain 进去。
verify: 重跑后树层左右贴边且 engine-band bled=false；池塘画进垫边时日志为 bled=true 且文件保持引擎尺寸。
applies: 透明底道具拆层。背景仍走天空对齐。
aliases:
- 框位锁定
- content_cut
source:
  kind: conversation
---
需求来源：拆图层复检时池塘整块变小下移。玩家要求找到根因，从管线改掉，再重拆。

必须保持：叠回贴的是画面带，不是整张引擎画布。
画面带一对一进脚印，scale_mul=1。
垫边里的尖端可以伸出脚印，由画布裁掉。
不因为垫边被画上就把整张引擎图 contain 进脚印。
不按透明外接矩形居中，也不为幽灵 MAE 做 NCC 缩小。

适用：引擎画布和裁切比例不同的部件层。入口是 isolate 之后的垫边处理和 compose 的贴回。
