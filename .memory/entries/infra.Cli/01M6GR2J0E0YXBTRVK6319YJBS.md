---
id: 01M6GR2J0E0YXBTRVK6319YJBS
module: infra.Cli
entity: AtlasWorkbench
kind: feature
status: active
supersedes: []
anchors:
- build_atlas.py
- atlas_reveal.py
- pmem_art.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 工作台：左右切图、并列参考、进化过程与设为终稿
verify: python -m unittest tests.test_atlas_all_images -v
applies: 使用 art-atlas 放大预览时
aliases:
- 进化过程
- 设为最终交稿
- 并列参考图
verified: '2026-11-04'
verified_at: '2026-11-04T19:32:04.024+08:00'
---
需求来源：放大预览要左右切图、并列参考、进化过程；过程图/原图别单独占画廊；进化里可设为最终交稿。
必须保持：
1) 放大预览左右按钮与方向键切当前筛选定稿；
2) 「并列参考图」无参考时置灰；有则左右并列；
3) 「显示进化过程」列出会话全部过程图+提示词/分数/轮次；
4) 「设置为最终交稿」把过程图像素覆盖终稿槽位，converge 轮次提示词保留，工作台定稿立即变成该图；
5) 主画廊不展示 process/reference（workbench_hide），侧栏只留定稿/废案。
适用条件：art-atlas 工作台。
入口：放大预览条；atlas_reveal /api/promote；pmem_art.attach_converge_prompt_traces。
