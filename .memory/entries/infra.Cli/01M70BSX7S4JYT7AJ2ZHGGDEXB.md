---
id: 01M70BSX7S4JYT7AJ2ZHGGDEXB
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes: []
anchors:
- build_atlas.py#viewerStep
- build_atlas.py#viewerEvoStep
- build_atlas.py#openViewer
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: 放大层大按钮定稿、底栏切进化
verify: python3 -m pytest tests/test_atlas_all_images.py -k 'not reveal_serves' -q
applies: art-atlas 工作台放大预览左右切换
---
# 放大层双链导航

## 需求来源
主画廊点定稿放大后，大左右按钮误切本图进化轮次；应切相邻定稿。底栏小 ←→ 才切进化。详情·进化对照里点图放大，大按钮切进化保持正确。

## 必须保持
1. 主画廊 openViewer(path)：_viewerNavMode=gallery，大按钮(ivPrev/ivNext/方向键)走 galleryNavPaths()；
   底栏 ivPrevBtn/ivNextBtn 走 viewerEvoStep + _viewerEvoPaths。
2. 详情对照 fromDetail / renderDetailMain：_viewerNavMode=evolve，大按钮切对照链；无会话时保留 examples 链，禁止回落 galleryNavPaths。
3. 教学 fromTeach：大按钮切教学样例链。
4. 主画廊定稿链查找 exactOnly，避免进化中图 basename 误命中定稿；大按钮相对 _viewerAnchorPath 步进。

## 入口
build_atlas.py：viewerStep / viewerEvoStep / openViewer / findViewerPathIndex；生成物 art-atlas.html。
