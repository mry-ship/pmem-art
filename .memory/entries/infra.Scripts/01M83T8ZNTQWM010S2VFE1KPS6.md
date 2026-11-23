---
id: 01M83T8ZNTQWM010S2VFE1KPS6
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M80RELEASE017ART
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py
- README.md
- USER_MANUAL.md
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 当前用户包版本是 v0.16.18-art（计分对账）
scope: project
verify: rg VERSION pmem_art.py；dist/pmem-art-0.16.18-art.zip 不含 .memory
applies: 向画师发放用户包或写版本说明时
aliases:
- 0.16.18-art
- v0.16.18-art
source:
  kind: conversation
---
现象：0.16.17-art 之后，正式分被硬顶压低时六维仍可能显示 9.6；计分后换文件仍能 finish；同一份字节能登记到另一轮；竖图文件名带 strip 会被当成横条。
结论：对外发放与 README、USER_MANUAL、skills-homepage 对齐的当前用户包版本为 v0.16.18-art。
打用户 zip：pyw -3 -u scripts/pack_pmem_art.py，产物 dist/pmem-art-0.16.18-art.zip；zip 不含 .memory 与 pmem hook。
GitHub Release 标签 v0.16.18-art。
证据：pmem_art.py VERSION=0.16.18-art。
计分对账见 skills_kit/scoring.py#cap_reported_dims 与 skills_kit/converge.py#_finish_plate_replaced。
