---
id: 01M6JW8BE2JSH46ZE4FJXBC6H1
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes: []
anchors:
- atlas_index.py
- atlas_reveal.py
- .memory/modules.yaml
revision: git:7f67ea9
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: infra.Cli 登记 atlas_index/reveal 根文件
verify: pmem doctor 模块覆盖率 100%；paths 含 atlas_index.py atlas_reveal.py
applies: 改工作台索引/定位桥接或 modules.yaml 覆盖率时
---
需求来源：项目体检发现根目录 atlas_index.py、atlas_reveal.py 未进 modules.yaml，覆盖率缺 2 文件。
必须保持：工作台索引与 localhost reveal 桥接仍属 infra.Cli；
与 build_atlas.py 同模块检索。
适用：维护 art-atlas / 打开工作台脚本。
入口：modules.yaml → infra.Cli.paths。
