---
id: 01M6K7V71NTWPE2VYN66N12Z8T
module: infra.Cli
entity: ValidateMatch
kind: correction
status: active
supersedes: []
anchors:
- atlas_index.py#match_module
- pmem_art.py#load_project
revision: git:8d36bd0
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 资产模块匹配改为最具体路径优先
verify: python -m pytest tests/test_module_path_match.py -q；pmem_art.py validate exit
  0
applies: validate/atlas/search 按 path 归模块时
---
旧匹配用模块字典顺序，后命中覆盖先命中，宽 glob（assets/scene/**）会盖住更具体模块，导致校验规格错配。
现按字面长度/通配更少优先，同分再比 active、模块点号深度。
同 glob 时更深模块名胜出（如 ui.MainMenu 胜 ui.HUD）。
