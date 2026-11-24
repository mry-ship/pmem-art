---
id: 01M843RCRP0J3N0QQ7BAX9EPXY
module: infra.Scripts
entity: LayerSplitEdgeClip
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/gate.py#_edge_clip_ratio
- scripts/pmem_layer_split/post_isolate.py#_letterbox_keep_trim
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: edge_clip按边框像素占比算，直切一整边仍可低于0.018
verify: 05-pond_boat.png 不透明框左缘为0，内容高度约一半贴左缘，edge_clip仍约0.0016
applies: 拆图层 isolate 之后 letterbox，再用 edge_clip 判切肢
aliases:
- 池塘左切
- edge_clip漏报
source:
  kind: conversation
---
现象：assets/mole_garden_resplit/new/05-pond_boat.png 池塘左缘和船左侧被直切，layer_status 里 edge_clip 仍是 0.0016。
原因：重抽 keep 写了 open on the left and bottom edges，并去掉 closed floating oval，模型把左边开口画成主体冲出左画布。
post_isolate._letterbox_keep_trim 按 alpha 外接矩形裁掉空白后，切口变成精灵左缘。
gate._edge_clip_ratio 用外圈 2px 不透明像素除以全部不透明像素，一条竖切只占很薄的质量。
这张 1024x1747 实测不透明框左缘 x=0，内容高度约 51% 贴左缘，比值仍约 0.0016，低于 0.018。
feat_match 0.66 也过了 0.55。
影响：主体被直切一整边时完整性闸不会脏，只剩幽灵 MAE。
