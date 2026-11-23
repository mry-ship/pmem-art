---
id: 01M83QEDHJR4QZ13DHC4FBZP5A
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes:
- 01M83PQMKNB7HD37RK3VKFK5Q5
anchors:
- scripts/pmem_layer_split/defaults.py#ISOLATE_PROMPT
- scripts/pmem_layer_split/isolate.py#_prompt_for
- scripts/pmem_layer_split/gate.py#_feat_match
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 拆层还原失败根因是完整性重画，失败句被写进删除项
verify: 对照 ISOLATE_PROMPT 第5条与 isolate._prompt_for 的 extra_remove；展陈二轮后 foreground
  fill=0.999 且 ghost mae 从 49.0 升到 50.1
applies: 走 gpt-image 隔离再 compose 贴回的 /pmem-layer-split
aliases:
- 拆层根因
- 重画补全
- extra_remove
source:
  kind: code
---
展陈拆层还原失败的根因是隔离合同让生成模型把裁切块重画成完整主体。
ISOLATE_PROMPT 第5条要求被裁切或遮挡的部分补全并留透明边；
compose 只能 contain 缩进冻结脚印，新轮廓回不到原图。
池塘被补成完整椭圆，前景草地与「禁止整片地毯」冲突后铺成实心草板，背景 HOLE FILL 重绘整幅草坪。
feat_match 只比蒙版下颜色和直方图，同风格重画 0.59–0.69 仍高于 0.55；
bg_bake 在框内差越大越接近 0，新草坪算合格空舞台。
重抽更差是因为 isolate._prompt_for 把 dirty 原因接进 MUST REMOVE，完整性条款仍在，前景 fill 从 0.72 画到 0.999，幽灵 MAE 从 49.0 升到 50.1。
ok 与 dirty 重叠只是 apply_ghost_dirty 在失败时把 hot 前 5 个 id 写入 dirty_ids，放大了重抽范围。
