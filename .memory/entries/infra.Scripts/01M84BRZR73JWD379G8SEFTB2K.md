---
id: 01M84BRZR73JWD379G8SEFTB2K
module: infra.Scripts
entity: LayerSplitBandLock
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/compose.py#place_band
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 垫边画布被 contain 进脚印，主体就会缩小下移。
verify: 池塘叠回 top 约 0.51、高约 0.49、fill=1.00。
source:
  kind: code
---
主体变小下移的根因是垫边和脚印被当成了同一张图。
模型把池塘画进左右黑垫后，旧逻辑留下整张引擎画布，叠回再把这张更宽的画布 contain 进脚印。
主体因此缩小，底对齐再把它往下挪。
池塘从 top 0.51、高 0.49 变成 top 0.57、高 0.43。

处理：只切空白垫边，画面带一对一贴脚印。尖端可以伸出框。重拆后池塘回到 top 0.51、高 0.49，fill=1.00。窗格、表情、斑点仍会重画，那是生成像素，不是框被缩放。
