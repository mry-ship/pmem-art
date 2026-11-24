---
id: 01M8737ZV0DQT4N1M2X97BRDQD
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M871W494Q42WSG345W5AXK7B
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py#pack
- scripts/pack_pmem_art.py#assert_pack_clean
revision: git:164d016
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 当前用户包版本是 v0.16.21-art（修订号、解码、多会话）
verify: rg VERSION pmem_art.py；gh release view v0.16.21-art；zip 不含 /.memory/
applies: 对外发放用户包、写下载链接时
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
结论：对外发放与 README、USER_MANUAL、skills-homepage 对齐的当前用户包版本为 v0.16.21-art。
打用户 zip：py -3 -u scripts/pack_pmem_art.py，产物 dist/pmem-art-0.16.21-art.zip。
本版含合同修订号校验、通用分不越界、成图解码验收、多会话活动索引、准备失败清指针、损坏会话占槽、心跳、资产哈希、表情路由补词。
GitHub Release 标签 v0.16.21-art，资产已上传。
证据：pmem_art.py VERSION=0.16.21-art；提交 164d016；zip 条目 990，无 /.memory/、无 pmem.mdc。
