---
id: 01M750C5HHHMNDH58AM7BD2BHT
module: feature.Improve
entity: WarmStartGuardrails
kind: exclusion
status: active
supersedes: []
anchors:
- improve/warm_start.py#build_warm_start_pack
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 禁止把旧recipe「优先复用」写进生图prompt
verify: tests.test_warm_start_guardrails.TestBuildPackIntegration 断言 prompt_block
  无「优先复用定稿方向」
applies: build_warm_start_pack 生成 prompt_block 时
aliases:
- 优先复用定稿方向
source:
  conversation: 7f6eb6c5-c94f-491f-9845-6667f9d3d230
---
现象：暖启把同模块旧 overview recipe 摘要贴进 prompt「优先复用定稿方向」，执行侧把旧档序/旧像素身份当成本趟选题底稿。
排除：prompt_block 再列出 top_recipes 或「优先复用定稿方向」句；旧 recipe 只可参与置信与 UI 展示。
允许：红线、过滤后 keep、审美拍板、口味、知识卡仍可注入。
与 NoSilentReusePriorDeliverable 互补：那边禁旧交付路径；这边禁记忆侧旧整表身份灌词。
