---
id: 01M77SY5WM7JDXFQ27ASD76R0W
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py#filter_keeps_for_task
- improve/warm_start.py#merge_conflict_taste_phrase
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 暖启再拦旧光泽卡通3D与他趟SKU身份
verify: unittest tests.test_warm_start_guardrails.TestKeepPhrases.test_merge_drops_foreign_sku_and_legacy_gloss
applies: build_warm_start_pack / filter_keeps_for_task 向 merge.* 注入时
source:
  conversation: b184581b-9d2c-4d9d-9f09-b09811f9f431
---
需求来源：提示词方向漂移审计——keep 仍可能灌入旧「光泽卡通 3D」与 HarborHotCocoa 等他趟具体档序身份。
必须保持：merge.* 的 _MERGE_CONFLICT_TASTE 拦截光泽卡通3D/硬卡通3D/硬镜面CGI/glossy cartoon 3D；
filter_keeps 对 goal 无重叠的 _PRIOR_SKU_IDENTITY（HarborHotCocoa/露莓果酱/L1 empty 等）丢弃；
旧 recipe 仍不进 prompt_block。
适用：converge generate 并入 Warm-Start 时。
入口：improve/warm_start.py filter_keeps_for_task / merge_conflict_taste_phrase。
