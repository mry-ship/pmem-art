---
id: 01M6RF4TYHANDCQZ9QRP0KDH0G
module: infra.Tests
entity: ParamValidation
kind: conclusion
status: active
supersedes: []
anchors:
- tests/test_param_validation.py#test_correct_configs_pass_for_all_four_cases
- comparison/style_refs/style_ref_02_pastel_sketch.png
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 四案例合同测靠三张最小画幅 PNG，不能删
verify: python -m unittest tests.test_param_validation.TestCaseParameterValidation.test_correct_configs_pass_for_all_four_cases
  tests.test_param_validation.TestCaseParameterValidation.test_wrong_aspect_ratio_raises
applies: 跑 Case 01–04 参数校验测例时
aliases:
- style_ref_02
- style_ref_03
- web_ref_01
- 参考图
source:
  conversation: d0bd94be-2445-43db-99f2-fed53b9d8564
---
comparison 里除 style_ref_01 外，Case 02/03/04 的参考图曾不在 git，test_param_validation 的存在性与画幅断言因此 FileNotFoundError。校验先查文件再查画幅。
现补的是纯色最小 PNG，只满足文件名和像素画幅：style_ref_02 与 web_ref_01 为 640x480（4:3），style_ref_03 为 480x640（3:4）。
偏差超过 15% 或横竖反了会失败。不要换成 Case 01，也不要删成空文件。
