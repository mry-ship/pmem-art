---
id: 01M7W6QV6HYQDAE7H3A0RRCGMF
module: infra.Scripts
entity: LayerSplitPipeline
kind: exclusion
status: active
supersedes:
- 01M7W5C5GK4603XNFBGVXVX6HK
anchors: []
revision: git:65977a3
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 排除：只letterbox不开autofit；gate ok当终审；遮挡残crop硬抽
verify: SKILL §4.2 排除表；post_isolate+compose autofit 默认
applies: 执行 /pmem-layer-split 定块与交件时
---
排除三件事（后续任意拆分）：
1) 只按脚印 letterbox、compose.autofit=false → 主体被撑满大脚印，幽灵变差。
2) 把 gate ok（asp/fill）当终审 → 背景烤脏与换样（帐篷变幔帐）会漏。
3) crop 大半被邻居挡住仍硬 isolate → 模型另造完整但不同件。
应：normalize(letterbox)+默认 autofit；§4.1 目视+bg_bake；遮挡重先收邻居边再抽。
