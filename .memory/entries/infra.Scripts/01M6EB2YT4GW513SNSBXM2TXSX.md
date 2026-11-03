---
id: 01M6EB2YT4GW513SNSBXM2TXSX
module: infra.Scripts
entity: LayerSplitPipeline
kind: feature
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/cli.py#_use_local_bg
- scripts/pmem_layer_split/defaults.py
- .cursor/skills/pmem-layer-split/SKILL.md
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-02'
summary: 默认 image2.5 背景；split_plan 先紧后扩只改点名边
verify: pipeline 默认 isolate 含 bg；--bg-local 才本地挖洞；SKILL §1.1/§3
applies: 执行 /pmem-layer-split 或拆层叠回时
---
需求：默认背景必须用 image2.5 出锐利空舞台；本地挖洞易糊，仅 --bg-local / run-local。split_plan 估框改为先紧后扩+只改点名边，禁止整表乱拧。
必须保持：非背景隔离仍 gpt-image-2.5；size 仅三档；叠回 contain+底对齐；合同在 SKILL。
行为：pipeline/isolate 默认含 bg（BG_ISOLATE_PROMPT）；
skip_bg 仅在 --bg-local；
曾 local_dig 的 bg 在 API 模式会重抽。
定块：pad≤0.02，setup 看 guide，单边微调。
入口：python scripts/run_pmem_layer_split.py --job assets/<job> pipeline
