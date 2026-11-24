---
id: 01M844HF7JST49FECAK3YCQ2WW
module: infra.Scripts
entity: LayerSplitFrameLock
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/post_isolate.py#_letterbox_keep_trim
- scripts/pmem_layer_split/compose.py#autofit_scale_to_ref
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆层叠回丢掉裁切里的位置，只等比缩小，跨度对不齐
verify: 池塘 scale_mul=1 且左缘贴内容框；树屋 scale_mul=0.66 且横枝够不到屋顶
applies: 拆图层 isolate 后 letterbox 再按脚印底对齐叠回
aliases:
- 横枝够不到
- 拆层位置丢失
source:
  kind: conversation
---
现象：同一套拆层里，池塘层左缘被直切后仍贴进脚印，树屋层横枝够不到原图屋顶。
原因：技能把「像那一件」和「在裁切里的位置」拆开。
isolate 允许主体在画布里重居中；
post_isolate._letterbox_keep_trim 再按 alpha 外接矩形裁掉空白并居中垫回比例，裁切里靠左还是靠右的信息没了。
compose.autofit_scale_to_ref 只在底对齐前提下从 1.0 缩到 0.66，按脚印区域的 NCC 挑尺寸。
池塘因此把切口当成精灵左缘、scale_mul=1.0 贴满；
树屋脚印含被枝条跨过的小屋，重画后的树被收成一块，NCC 选了 0.66，横枝跨度一起缩小。
edge_clip 只算文件最外 2px 的面积比，feat_match≥0.55 即过，技能又规定 scale_mul 低于 0.75 不要为尺寸重抽，所以这种错位不会被拦。
影响：所有「矩形框包进邻居、主体却是细长或偏在一侧」的层都会这样，不限这一张花园。
