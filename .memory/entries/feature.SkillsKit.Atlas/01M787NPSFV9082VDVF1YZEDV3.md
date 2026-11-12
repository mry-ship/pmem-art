---
id: 01M787NPSFV9082VDVF1YZEDV3
module: feature.SkillsKit.Atlas
entity: ClassifyWatchSkipStaging
kind: exclusion
status: active
supersedes: []
anchors:
- lifecycle.py#list_image_files
- lifecycle.py#is_skill_staging_dirname
- classify.py#cmd_watch_sync_classify
- atlas_index.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: classify-watch 禁止扫走 skill_YYYYMMDD_* 清点目录
verify: python -m unittest tests.test_memory_fs.TestJunkSidecarSkip.test_list_image_files_skips_skill_staging_suite
  -q；classify-watch 日志不应列出 skill_*_suite/out
applies: pmem-atlas / classify-watch 扫描 assets 时
aliases:
- 清点目录误搬
- suite被归档
- classify-watch搬家
source:
  conversation: 679ccb52-31d7-4ad3-8b43-02f24338f778
---
现象：/pmem-atlas 跑 classify-watch --apply 把 assets/skill_20261112_suite/out 成图挪进 assets/ui/** 并同名覆盖，清点终稿被拆散。
排除：dirname 匹配 skill_\d{8} 的清点/任务交付根（含 *_suite）不进 list_image_files、classify-watch 队列与 atlas_index 扫描；
要归档须玩家点名搬出或手工 ingest，禁止全库 watch --apply 吞清点目录。
与 ClassifyWatchSpecDrift（规格锁死）互补：那是入库后 specs 问题，这条是根本不该扫清点根。
