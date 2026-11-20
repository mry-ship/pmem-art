---
id: 01M7WHTJGJ8KSN67BPFP2EYMJY
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M7QD8M1Q5HZ88YFDTBYXCRT9
- 01M7WETYRM1C8ZSRZ4BEMZG5GJ
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py#should_skip
- skills_kit/skill_registry.py
- scripts/pmem_layer_split/defaults.py
revision: git:e02ba76
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 当前用户包版本是 v0.16.14-art，含 /pmem-layer-split（11 技能）
scope: project
verify: rg "VERSION =" pmem_art.py；pyw -3 -u scripts/pack_pmem_art.py 后 zip 内应有 scripts/pmem_layer_split/defaults.py
  与 */pmem-layer-split/SKILL.md，且无 assets/*/split_plan.json
applies: 向画师发放用户包或写版本说明时
aliases:
- 0.16.14-art
- v0.16.14-art
- layer-split release
- 拆图层发包
source:
  conversation: 2f354fef-48d1-45fb-b2ba-e9001d9d3e16
---
现象：0.16.13-art 之后合入拆图层技能与管线加固（footprint/autofit、isolate pad、midground 槽位、用户包跳过 assets/*/split_plan.json 作业目录）。
结论：对外发放与 README/USER_MANUAL/skills-homepage 对齐的当前用户包版本为 **v0.16.14-art**；
技能总数 11（含 /pmem-layer-split）。
打用户 zip：`pyw -3 -u scripts/pack_pmem_art.py`，产物 `dist/pmem-art-0.16.14-art.zip`；
GitHub Release 标签 `v0.16.14-art`。
证据：`pmem_art.py` VERSION=`0.16.14-art`；pack should_skip 含 split_plan 作业；三端技能/命令/registry 已装 layer-split。
影响：画师装包与文档版本号以此为准；0.16.13 及更早包不含本技能闭环加固。
