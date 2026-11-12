---
id: 01M787P2ME32TGY4GKK0DCH13M
module: feature.SkillsKit.Atlas
entity: AtlasApprovalBoundary
kind: feature
status: active
supersedes:
- 01M6P44XW3AJRKMC748939KBZ8
anchors:
- classify.py#cmd_watch_sync_classify
- lifecycle.py#list_image_files
- pmem_art.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 高置信自动归档；skill_YYYYMMDD_* 清点根不进 watch
verify: classify-watch 不列出 skill_*_suite；unittest tests.test_memory_fs…skips_skill_staging_suite；高置信仍可
  ingest 非清点散图
applies: 调用 /pmem-atlas 且 watch_dirs 中存在未映射图片时
aliases:
- classify-watch
- 自动归档
source:
  conversation: 679ccb52-31d7-4ad3-8b43-02f24338f778
---
需求来源：统一 /pmem-atlas 合同，并堵住清点目录被 classify-watch --apply 搬走。
必须保持：明确调用 /pmem-atlas 即授权 classify-watch 自动归档；
仅自动 ingest 高置信度候选；
低置信度或无法分类文件保持原位并说明；
空结果明确报告没有待归档散图；
dirname 匹配 skill_\d{8} 的清点/任务交付根跳过扫描与搬家；
归档后继续模块总览和刷新图谱。
入口：/pmem-atlas 三端 skill；pmem_art.py classify-watch → classify.cmd_watch_sync_classify；lifecycle.list_image_files。
