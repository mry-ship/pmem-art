---
id: 01M8732VDXG5PDSC0FW3N7NRCP
module: infra.Judge
entity: GeneralDimBounds
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#parse_5d_dims
- skills_kit/scoring.py#_as_ten_point
revision: git:7cd0f32
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 通用六维不跨维取分，超过 10 分就丢掉
verify: unittest tests.test_hard_pits_gates.TestGeneralDimBounds -q
applies: 解析通用构图/光影/透视/质感/风格/无瑕疵字符串或 composition= 这类键值时
aliases:
- 通用六维
- 10分
source:
  conversation: 220fd64e-811e-4d24-b7dd-92b712946c65
---
需求来源：通用尺的标签和分数之间用 [^0-9]*，会把下一维的分数吃进来；超过 10 分也会进入调和平均。
必须保持：标签后只允许不含下一维名称的短空白。分数小于 0 或大于 10.05 就丢掉这一维，正式分为空，不能用手填总分顶上。略高于 10 且不超过 10.05 的舍入压成 10。
入口：skills_kit/scoring.py parse_5d_dims。
