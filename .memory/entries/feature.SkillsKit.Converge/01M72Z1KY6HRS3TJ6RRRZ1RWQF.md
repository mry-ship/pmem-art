---
id: 01M72Z1KY6HRS3TJ6RRRZ1RWQF
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/prompt_scale.py#_infer_case_style_and_subject
- skills_kit/prompt_scale.py#get_converge_scale_profile
- skills_kit/prompt_scale.py#_constraint_tail
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 无垫图时去掉「保原图画风/性别物种」角色模板
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_no_ref_strips_keep_original_style_identity
applies: converge / compose_style_first 且本轮无垫图时；有垫图不改
aliases:
- 无垫图
- 保原图画风
- 角色模板
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
需求来源：jam-verify 整表无垫图（reference_image_paths 空）时，提示词仍拼进 prompt_scale 角色改图话术「保持原图画风笔触与色板；
保持原图性别、物种、年龄段」，模型把「原图」落到默认写实棚拍，且性别物种对果酱无意义。
必须保持：ref_image 为空时，forbidden_changes 去掉「保持原图画风 / 原图核心艺术媒介 / 性别、物种、年龄段」；
补上 style_surface「禁止回落写实棚拍」。
style 导语改为「品类默认画风优先」（merge）或「题材画风优先」，禁止写「原图画风优先」。
有垫图时仍保留原有角色改图锁。
入口：skills_kit/prompt_scale.py _infer_case_style_and_subject / get_converge_scale_profile；
经 compose_style_first_prompt 进生图句。
