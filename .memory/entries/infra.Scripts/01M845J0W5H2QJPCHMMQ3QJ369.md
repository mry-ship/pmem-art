---
id: 01M845J0W5H2QJPCHMMQ3QJ369
module: infra.Scripts
entity: LayerSplitInnerShrink
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/isolate.py#_prompt_for
- scripts/pmem_layer_split/post_isolate.py#_letterbox_keep_frame
- scripts/pmem_layer_split/gate.py#_feat_match
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 垫成引擎画布后再切已知垫边；画进垫边就不切，缩在带里由 inner_gap 标脏。
verify: 树层 inner_gap 左右为 0；池塘 bled=true 时文件仍是 1024x1536；鼹鼠上下间隙大于 0.15 则 dirty。
applies: 引擎只有三档尺寸、脚印比例对不上时成立。
aliases:
- 框内缩小
- 引擎画布比例
source:
  kind: conversation
---
引擎画布和裁切框比例不同。
道具主垫先垫成引擎画布，生成后只切已知垫边。
童话花园这次重跑：树的画面带左右贴边（inner_gap 左 0 右 0，上 0.085 下 0.131），结构闸通过。
池塘连续两次把主体画进左右垫边（左侧侵入约 51px / 60px），因此不切垫边，避免把池沿切直；
它在引擎画布里下沿只空 0.042，上沿 0.276 是去掉的小屋。
鼹鼠重抽后仍缩在带内（上下 0.33/0.30），inner_gap 能拦住。
提示词锁不住所有层，闸门只能标脏，不能把画进垫边的像素挪回去。
