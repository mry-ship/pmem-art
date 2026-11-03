---
id: 01M6GXBXE4VHFRJN60XAYB4YM3
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes:
- 01M6GR2J0E0YXBTRVK6319YJBS
anchors:
- build_atlas.py#resolveMediaSrc
- build_atlas.py#buildLineageExamples
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 工作台进化对照与小图显示
verify: python -m unittest tests.test_atlas_all_images -v
applies: 使用 art-atlas 放大预览时
---
需求来源：放大预览进化对照；原图卡要挂分析。
必须保持：
1) 详情原图卡展示原图不足/为何要出下一张（ref_analysis、R1 抽出的原图分析、否则据此开跑+goal）；
2) 原图不显示误导性「无 Prompt」；可复制「原图分析」；
3) resolveMediaSrc/eager/缺图占位等既有小图规则仍保持；
4) 主画廊不单独展示 process/reference。
入口：enrichOriginalMeta；attach_converge.ref_analysis；renderDetailPipelineHtml。
