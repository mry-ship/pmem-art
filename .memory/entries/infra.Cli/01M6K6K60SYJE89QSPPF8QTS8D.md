---
id: 01M6K6K60SYJE89QSPPF8QTS8D
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes: []
anchors:
- atlas_index.py#classify_plate
- pmem_art.py#attach_converge_prompt_traces
- build_atlas.py#assetPlate
revision: git:8d36bd0
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 主画廊只定稿；原图/过程只进进化对照
verify: python -m unittest tests.test_classify_plate_gallery -q；Test 画廊无 01_style/r1_916
applies: 使用 art-atlas 主画廊与进化对照时
---
需求来源：用户发现原图也在工作台主画廊显示。必须保持：
  1) classify_plate 把 rN_916/concept_r1 等过程图、01_style/ref/refs/ 原图垫图标成 process/reference；
  2) 会话 winner 强制 plate=final 且可见；
  3) 前端 assetPlate 同规则，会话 ref 即使误标也不进主画廊。
适用：art-atlas 主画廊。
入口：atlas_index.classify_plate；
pmem_art.attach_converge_prompt_traces；
build_atlas.isWorkbenchHiddenAsset。
