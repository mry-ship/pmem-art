---
id: 01M83RFEPS946KYM1TDQ7SN5EQ
module: infra.Scripts
entity: LayerSplitPipeline
kind: feature
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/gate.py#run_gate
- scripts/pmem_layer_split/qa.py#apply_ghost_dirty
- scripts/pmem_layer_split/cli.py
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆层闸不再因略小重抽，失败句不进删除项
verify: scale_mul<0.75 只打印 NOTE；ghost-only 时 pipeline 打印 stop 且不 isolate
applies: 跑 layer-split gate、isolate、pipeline 或 retry-dirty
aliases:
- scale_mul
- extra_remove
source:
  kind: code
---
需求来源：同一次展陈。略小被重抽，闸门句子被写进删除项，整图失败时热度前 5 层被塞进 dirty_ids，pipeline 会把已经对齐的层盲重画。
必须保持：scale_mul 低于 0.75 只打印 NOTE，不 dirty。
isolate 不把 reasons 写入 remove。
整图失败不再把未过层阈值的 id 写入 dirty_ids。
pipeline 和 retry-dirty 遇到只有 layer_ghost_mae 的层就停，等把错的零件写进 keep/remove 再 isolate --ids。
背景补洞只补道具留下的洞，花和光斑留住。
裁切补全不得换成另一件产品图。
适用：layer-split 的 gate、isolate、qa、pipeline、retry-dirty。
入口：scripts/pmem_layer_split/gate.py、isolate.py、qa.py、cli.py、defaults.py。
