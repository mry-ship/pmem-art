---
id: 01M72SAEPJMT9SHSYRH87X0E3J
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py#stale_merge_inject_summary
- improve/warm_start.py#merge_conflict_taste_phrase
- improve/warm_start.py#filter_habits_for_task
- improve/warm_start.py#filter_keeps_for_task
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: merge 暖启过滤旧框高/纯黑 summary，并丢弃反 GH taste
verify: unittest tests.test_warm_start_guardrails.TestMergeConflictTaste tests.test_warm_start_guardrails.TestOffTopicEntries.test_stale_merge_volume_summary_flagged
applies: merge.* 开 converge 暖启 / build_warm_start_pack 时
aliases:
- merge conflict taste
- 反 GH 词过滤
- 油腻高光过滤
- 机读框高
- 纯黑隔离底
source:
  conversation: 47f6bbb9-8756-4463-9252-553fb8630b97
---
需求来源：旧 merge recipe/redline 的框高阶梯、机读框高数字句、纯黑隔离底会污染暖启；GH 手绘/软光泽目标又被 taste「廉价塑料感/油腻高光」「体量递增」「黑空底」「哑光缎面」等反向拖偏。
必须保持：
1) stale_merge_inject_summary 拦旧框高/纯黑类 summary（含机读框高数字句、框高回退句）；
2) merge.* 在 filter_habits_for_task / filter_keeps_for_task 丢弃 _MERGE_CONFLICT_TASTE 命中短语；非 merge 模块行为不变。
入口：build_warm_start_pack → converge generate 并入已过滤 pack。
适用条件：module.startswith("merge.")。
