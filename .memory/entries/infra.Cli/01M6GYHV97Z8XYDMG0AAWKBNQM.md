---
id: 01M6GYHV97Z8XYDMG0AAWKBNQM
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes:
- 01M6GXBXE4VHFRJN60XAYB4YM3
anchors:
- atlas_reveal.py#purge_paths_from_atlas_sidecar
- build_atlas.py#syncTrashFilterIntoData
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 删除进垃圾桶须同步踢掉 atlas 索引，刷新才不会回来
verify: python -m unittest tests.test_atlas_all_images.AtlasAllImagesTests.test_delete_purges_atlas_sidecar_so_refresh_stays_gone
  -v
applies: 工作台删除后刷新/热更新
aliases:
- 删了又回来
- 刷新回来
---
需求来源：确认删除进垃圾桶后，刷新网页图又出现。
根因：只改了页面内存 DATA，.memory-art/atlas_data.json 与 HTML 内嵌索引仍留着；
热更新/刷新会把旧索引加载回来。
必须保持：delete_paths 成功后 purge atlas_data.json；
启动与 hotReload 按 _trash/manifest.json 再滤一遍。
文件仍在垃圾桶可找回。
