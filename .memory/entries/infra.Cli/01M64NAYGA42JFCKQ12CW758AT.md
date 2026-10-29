---
id: 01M64NAYGA42JFCKQ12CW758AT
module: infra.Cli
entity: AtlasAllImages
kind: feature
status: active
supersedes:
- 01M64KPMJERH4XKZ4926ACXKK6
anchors:
- atlas_index.py#merge_index_into_assets
- build_atlas.py
- pmem_art.py
- tests/test_atlas_all_images.py
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: 所有图归总默认今天；散图归其他仅工作台可见不写recipe
verify: python3 -m unittest tests.test_atlas_all_images -v；HTML 含「所有图归总」与「其他」
applies: 生成或 silent refresh art-atlas 工作台时
aliases:
- 所有图
- 散图
- 其他
- 工作台可见
source:
  conversation: 7e5e2160-95b3-4c29-934e-6fa0f52ed769
---
需求来源：美术要在工作台看到 Cursor/converge 散图，但不自动写成正式 recipe。
必须保持：左侧最上「所有图归总」；二级默认今天，可切昨天/更早/全部时间与类型；散图 category=misc，展示名「其他」，只工作台可见；可见≠正式 ingest，不因索引写 recipe。
适用条件：生成或 silent refresh art-atlas 时。
入口：python3 pmem_art.py atlas；双击 art-atlas.html。
扫描仍覆盖 assets/.cursor/generated/generated/converge；docs/showcase 等主动指定路径仍不进归总。
