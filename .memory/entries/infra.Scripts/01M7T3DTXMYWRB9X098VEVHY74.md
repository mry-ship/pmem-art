---
id: 01M7T3DTXMYWRB9X098VEVHY74
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/calibrate.py
- scripts/pmem_layer_split/compose.py#place_scaled
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-19'
summary: 叠回锚点：踩地底齐、墙挂居中、吊灯顶齐；禁止为过闸撑框
verify: truth_boxes 里 dartboard anchor=center、chandelier=top-center；compose 日志打印对应
  anchor
applies: 拆层 setup/compose 摆位时
aliases:
- 摆位
- anchor
- top-center
---
摆位漂的根因之一：calibrate 曾把所有层写成 anchor=bottom-center，盖掉 grounded=false，飞镖/吊灯被拽到底。
现规则：plan.anchor 优先；吊灯类 → top-center；ungrounded → center；否则 bottom-center。compose.place_scaled 支持这三种。
另一根因：为过 fill/asp 把脚印撑大（沙发框拉到全宽）导致槽位错乱——禁止，应重抽精灵。
位置锁优先于闸门数字。
