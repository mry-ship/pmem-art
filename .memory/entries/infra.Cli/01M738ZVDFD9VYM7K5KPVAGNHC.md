---
id: 01M738ZVDFD9VYM7K5KPVAGNHC
module: infra.Cli
entity: ModuleCoverage
kind: feature
status: active
supersedes: []
anchors:
- .memory/modules.yaml
- pmem_art.py#load_project
- art_cli.py
- art_shell_hook.py
revision: git:8ab2d7f
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: art_cli/art_shell_hook 入 modules；条目非图不进图片QA
verify: pmem doctor 覆盖率 100%；validate 对 assets/ui/soft/preview.html 不再 FAIL
applies: 本仓库模块登记与资产质检
aliases:
- 覆盖率
- preview.html
- 非图sidecar
source:
  conversation: 813b285a-1cff-4227-bdd6-587c9e0528e2
---
需求来源：项目深度体检要求模块覆盖率 100%、validate 无硬 FAIL。
必须保持：
1) .memory/modules.yaml 的 infra.Cli.paths 含 art_cli.py、art_shell_hook.py。
2) load_project 从记忆条目收集资产时，后缀不在 png/jpg/jpeg/webp 的 sidecar（如 preview.html）不进 asset_Set，不做分辨率/通道 QA；文件可仍挂在条目上作说明。
适用条件：pmem doctor 覆盖率与 pmem_art validate/doctor。
入口：.memory/modules.yaml；pmem_art.py load_project 资产收集循环。
