---
id: 01M7WC7VV4H3K0QNJJPB1VG5EQ
module: infra.Scripts
entity: LayerSplitPipeline
kind: correction
status: active
supersedes:
- 01M7W6RHQ400142A69K7XG92E3
anchors:
- scripts/pmem_layer_split/gate.py#_bg_bake_score
- scripts/pmem_layer_split/defaults.py
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 空舞台清影渍+禁英雄树；bg_bake=NCC×MAE≤0.58；接地影跟物件
verify: _skill_check3 RESULT PASS；gate._bg_bake_score 含 mae；viking gate ok=10；_ghost_qa
  level!=fail 或 warn
applies: 执行 /pmem-layer-split 任意 job
aliases:
- 空舞台
- bg_bake
- 接地影
- 英雄树
- flat_median
---
玩家要求技能通用改善，并复查无误。

合同：
1) grounded 物件必须带同向柔接地影（影属精灵）。
2) 空舞台去道具时连带去影渍；远树远且小；禁两侧英雄树；空地保持开阔。
3) bg_bake_max=0.58；计分改为 NCC×MAE 权重（脚印含远树/天空时纯 NCC 易误报）。
4) 密集场景本地挖洞 dig_frac 过高会 flat_median 毁掉空舞台——禁止当默认交付底。

viking_camp_10 复查：gate 10/10 ok；幽灵 MAE≈47.8 为 warn（未≥48 fail）。
