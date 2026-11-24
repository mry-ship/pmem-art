---
id: 01M86ZE012SR1KS3SKFQNYRBZP
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M83T8ZNTQWM010S2VFE1KPS6
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py#iter_source_files
- scripts/pack_pmem_art.py#assert_pack_clean
revision: git:c92cbb7
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 当前用户包版本是 v0.16.19-art（prepare 与门槛早停）
scope: project
verify: rg VERSION pmem_art.py；gh release view v0.16.19-art；zip 不含 /.memory/
applies: 向画师发放用户包或写版本说明时
aliases:
- 0.16.19-art
- v0.16.19-art
source:
  conversation: ba9d4a3d-e1c3-47a2-8066-198c30709ef1
---
现象：0.16.18-art 之后出图准备收成一次 converge prepare，门槛维仍低于合格线时早停；超过 36 小时未结束的旧会话不再占并行名额；桌面图标符号明显偏小会被拦住。
结论：对外发放与 README、USER_MANUAL、skills-homepage 对齐的当前用户包版本为 v0.16.19-art。
打用户 zip：pyw -3 -u scripts/pack_pmem_art.py，产物 dist/pmem-art-0.16.19-art.zip。只收 git 已跟踪文件，再去掉 .memory 与 pmem hook。
GitHub Release 标签 v0.16.19-art，资产已上传。
证据：pmem_art.py VERSION=0.16.19-art；提交 c92cbb7。
开发仓仍带 .memory；只有用户 zip 去掉 pmem。
