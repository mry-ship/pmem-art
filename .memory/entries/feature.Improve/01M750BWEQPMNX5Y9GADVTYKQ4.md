---
id: 01M750BWEQPMNX5Y9GADVTYKQ4
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes:
- 01M72SAEPJMT9SHSYRH87X0E3J
anchors:
- improve/warm_start.py#build_warm_start_pack
- improve/warm_start.py#collapse_opposed_prefs
- improve/warm_start.py#filter_keeps_for_task
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 暖启：旧recipe不进生图词；过滤花园keep；冷暖去冲突
verify: py -3 -m unittest tests.test_warm_start_guardrails -v
applies: converge start/generate 注入 Warm-Start 时
aliases:
- Warm-Start
- 优先复用定稿方向
- 冷暖并列
source:
  conversation: 7f6eb6c5-c94f-491f-9845-6667f9d3d230
---
需求来源：水果 merge 收敛时 Warm-Start 把旧整表 recipe 写成「优先复用定稿方向」、妖精花园 keep、冷光源/暖光并列，把本趟提示词拖回旧轨。
必须保持（含既有）：
1) stale_merge_inject_summary 仍拦旧框高/纯黑类 summary；
2) merge.* 仍丢弃反 GH conflict taste；
3) 新增：top_recipes 只留 pack/置信，prompt_block 禁止「优先复用定稿方向」与 recipe id 列表；
4) merge 任务 filter_keeps 丢弃 fairy_garden 题材 keep（无货柜/糖釉锚点时）；
5) preferred_lighting / preferred_color_temperature 经 collapse_opposed_prefs，冷暖冲突时只留最新一极。
入口：build_warm_start_pack → converge generate 并入。
适用：所有 converge 暖启；merge 相关过滤仅 module.startswith("merge.")。
