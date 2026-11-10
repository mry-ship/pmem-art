---
id: 01M6RF4T5BA6ZG3TW1DXYQNKYC
module: infra.Scripts
entity: PackUserZip
kind: correction
status: active
supersedes:
- 01M6K708ZTW9MCQZ7WRP29MBCG
anchors:
- scripts/pack_pmem_art.py#should_skip
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 用户包不带 art-atlas.html，无瑕度写在 build_atlas.py
verify: python -m unittest tests.test_pack_pmem_art -v 的 zip 无 art-atlas.html，且 build_atlas.py
  含 flawlessness 无瑕度
applies: 给新项目分发用户 zip 并打开工作台
aliases:
- art-atlas.html
- 画廊
- 无瑕度
verified: '2026-11-11'
verified_at: '2026-11-11T01:15:57.631+08:00'
source:
  conversation: d0bd94be-2445-43db-99f2-fed53b9d8564
---
旧结论认为用户 zip 里要有一份 art-atlas.html，且其中第六维为无瑕度。
这条对 HTML 文件不成立。art-atlas.html 是各项目 atlas 现生成的，仓库 gitignore；pack 若照单打包磁盘已有文件，干净树会漏，本机有画廊又会泄。
现必须跳过该文件。无瑕度标签仍在 build_atlas.py，解压后跑 pmem_art.py atlas 才会得到工作台页。
0.16.2 的「完成度」误标仍只针对生成器源码，不靠预置 HTML。
