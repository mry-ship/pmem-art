---
id: 01M6K6RD6E1P08ZCFY000VSQKZ
module: feature.SkillsKit.Showcase
entity: Dim6Label
kind: correction
status: active
supersedes: []
anchors:
- build_atlas.py#TEACH_DIM_LABELS
- skills_kit/prompt_scale.py#_DIM_WEIGHT_ZH
revision: git:8d36bd0
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: 画廊第六维标签应为无瑕度非完成度
verify: TEACH_DIM_LABELS.flawlessness==无瑕度；parse 无瑕度/无瑕疵均可
applies: art-atlas 六维芯片与过程板中文维名
aliases:
- 无瑕度
- 完成度
- flawlessness
---
画廊/工作台六维芯片曾把 flawlessness 显示成「完成度」（build_atlas.py TEACH_DIM_LABELS，约 2026-11-03 教学层引入时写错）。
正确展示名是「无瑕度」；
计分与旧文案里的「无瑕疵」仍作同义词解析。
已改 build_atlas.py / art-atlas.html / prompt_scale 展示，并让 scoring、vlm_judge 同时认无瑕度与无瑕疵。
