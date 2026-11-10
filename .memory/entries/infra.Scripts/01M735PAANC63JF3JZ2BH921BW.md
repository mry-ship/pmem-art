---
id: 01M735PAANC63JF3JZ2BH921BW
module: infra.Scripts
entity: Packaging
kind: correction
status: active
supersedes:
- 01M70XGP75QQTYH1MQ0CTKSJFW
anchors:
- pmem_art.py
- scripts/pack_pmem_art.py
- README.md
- USER_MANUAL.md
revision: git:e5ebced
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 用户包已升到 v0.16.8-art，取代 0.16.7
verify: gh release view v0.16.8-art；zip 名 pmem-art-0.16.8-art.zip；VERSION==0.16.8-art
applies: 画师下载用户包 / Release 分发
aliases:
- 0.16.8-art
- 用户包
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
用户包已升到 v0.16.8-art（https://github.com/mry-ship/pmem-art/releases/tag/v0.16.8-art）。
zip 文件名是 pmem-art-0.16.8-art.zip。
0.16.7-art 仍可下载但不作为最新推荐。
本版：GenerateImage pre-gen 默认关闭且 ensure_cursor_stubs/install 不再装回；
merge Warm-Start 冲突 taste 过滤；
delivery gates / GH 参考文档与技能硬化。
用户包跳过 assets/skill_* 本地验证散图。
