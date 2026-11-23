---
id: 01M83PQMKNB7HD37RK3VKFK5Q5
module: infra.Scripts
entity: LayerSplitPipeline
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/qa.py#apply_ghost_dirty
- scripts/pmem_layer_split/gate.py#_bg_bake_score
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 展陈拆层幽灵失败时ok与dirty重叠，重抽可抬高MAE
verify: layer_status.json 中 ok_ids 与 dirty_ids 可同时含 treehouse_mole；_ghost_qa.json
  mae>48；qa.py 在 level=fail 时追加 hot[:5]
applies: 跑 /pmem-layer-split 且 ghost level=fail 时读 layer_status / RESULT
source:
  kind: code
---
2026-11-23 展陈 layer.split（童话花园 6 层）流程跑完，还原失败：ghost MAE 50.1（失败线 48），PSNR 11.1。
1) qa.apply_ghost_dirty 在整图 level=fail 时把 hot 前 5 个 id 追加进 dirty_ids，不改各层 status。
   终态 treehouse_mole 同时在 ok_ids 与 dirty_ids；
   mushrooms 已是 needs_human 仍在 dirty_ids。
   RESULT「gate 5/6 ok」只代表当时的脚印闸，不能当成终态账本。
2) 只重抽精灵会把脚印分数抬高、把还原打差：首轮 ghost MAE 49.0（pond 61.0 / foreground 56.5），二轮后 50.1（pond 62.9 / foreground 59.1）。
   foreground 的 fill 从 0.72 升到 0.999、scale_mul 从 0.85 升到 1.0，下半幅变成一块实心草地板。
3) 脚印闸看不出重画：各层 feat_match 0.59–0.69，都高于 0.55；bg_bake=0 只说明道具框里和原图差得够大，整幅重绘的草坪仍算空舞台合格。叠回是同风格重画再贴，原图轮廓对不齐。
