---
id: 01M6K708ZTW9MCQZ7WRP29MBCG
module: infra.Scripts
entity: PackUserZip
kind: conclusion
status: active
supersedes: []
anchors:
- scripts/pack_pmem_art.py
- dist/pmem-art-0.16.3-art.zip
revision: git:8d36bd0
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 用户包0.16.3起工作台第六维为无瑕度
verify: python -m unittest tests.test_pack_pmem_art；解压后 atlas+reveal 芯片为无瑕度
applies: 给新项目分发用户 zip 并打开工作台
aliases:
- 0.16.3-art
- 无瑕度
- 装包
---
新项目装用户包需用 0.16.3-art 起：zip 内 build_atlas.py / art-atlas.html 第六维为无瑕度；
解压后 `pmem_art.py atlas` 重生成与 atlas_reveal 托管后仍显示无瑕度；
立即刷新/自动刷新控件在页内。
0.16.2 及更早 zip 仍带完成度误标，勿再分发。
验证：_tmp_audit_pack 模拟解压+atlas+reveal HTTP 通过；tests.test_pack_pmem_art 断言无瑕度；tests.test_atlas_all_images 15 项 OK。
