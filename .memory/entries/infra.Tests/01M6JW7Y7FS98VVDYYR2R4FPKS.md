---
id: 01M6JW7Y7FS98VVDYYR2R4FPKS
module: infra.Tests
entity: ParamValidation
kind: conclusion
status: active
supersedes: []
anchors:
- tests/test_param_validation.py
- pmem_art.py#inspect_png
revision: git:7f67ea9
author: 1002378395@qq.com
note_date: '2026-11-04'
summary: JPEG 头解析测例改本地造图
verify: python -m pytest tests/test_param_validation.py::TestGateFixes::test_jpeg_header_has_resolution
  -q
applies: Case02 母版 JPG 不在仓内或被 slim 掉时
---
assets/character/pastelgirl/pmem_02_pastel_sketch_girl.jpg 与 aspect3x4 副本已不在 git。
合同测的是 inspect_png 读 JPEG 头出 resolution，应用临时 PIL 造 720x580 / 864x1152，勿再绑丢失资产路径。
