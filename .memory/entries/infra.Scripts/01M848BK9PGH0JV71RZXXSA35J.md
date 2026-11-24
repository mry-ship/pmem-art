---
id: 01M848BK9PGH0JV71RZXXSA35J
module: infra.Scripts
entity: LayerSplitSideSlice
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/post_isolate.py#_unpad_engine_band
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 垫边里的细尖要留下，不能整条切掉。
verify: 树屋重拆后藤尖闭合，右缘留白约 32px；side_cut_px 仍为 120。
applies: 裁切比 1024x1536 更瘦、左右有垫边的道具层。
aliases:
- 左右被切
- 贴边再切
source:
  kind: code
---
左右被切有两截，都出在「引擎画布比裁切更宽，左右是黑垫」的层上。

第一截：提示词要求主体去贴黑边。模型把伞盖、卷枝、池沿推到画面带边界，再整条切掉垫边，边界就变成直切。完整圆沿贴着自己的外接边大约 70 行，直切大约 170 行以上，所以 side_cut_px 用 120。

第二截：细尖（藤尖、卷须）只伸进垫边一小段，不透明占比低于 0.08，旧逻辑仍把整条垫边切掉，尖端被删。
闸门数不出这截，因为贴边行数可以只有几十行。
现在只切垫边里真正空白的部分，已经画上的尖端和 2px 晕边留下；
垫边被画满才整幅保留并标 engine_band_bleed。

树屋按这条重拆后，藤尖是收尖的完整曲线，离文件右缘约 32px；左卷枝也是完整螺旋。不要为了幽灵 MAE 再缩框。
