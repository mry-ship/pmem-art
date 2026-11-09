---
id: 01M70M0KZCFCZCV1W01A95Z9M0
module: feature.SkillsKit.Converge
entity: AspectWhitelistStart
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
- skills_kit/validate_params.py#validate_case_generation_params
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: start/无垫图硬拒非法 aspect；finish atlas 后台刷
verify: python3 -m unittest tests.test_param_validation.TestGateFixes.test_invalid_aspect_ratio_rejected_without_pad
  -q
applies: converge start/generate/finish
---
需求来源：merge 曾用 2:1 进会话；
finish 同步 refresh_atlas 在并发下挂数分钟。
必须保持：converge start/generate 在无垫图时也校验 VALID_ASPECT_RATIOS；
allow_empty_pad 同样硬拒；
finish 的 atlas 刷新改 daemon 线程，不阻塞结算输出。
