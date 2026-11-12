---
id: 01M75BVMTRMCJD43FZ1K1MX01W
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes:
- 01M750BWEQPMNX5Y9GADVTYKQ4
- 01M708NTJM15FT8XQ6X4GHVCX1
anchors:
- improve/warm_start.py#_foreign_artifact_bleed
- improve/warm_start.py#_soft_goal_overlap_ok
- improve/warm_start.py#habit_relevant_for_task
- improve/warm_start.py#filter_keeps_for_task
- tests/test_warm_start_guardrails.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 暖启串题：外国交付物痕迹同族剥离后才拦
verify: pyw -3 -m unittest tests.test_warm_start_guardrails -q
applies: converge start/generate 注入 Warm-Start 时
aliases:
- 串题过滤
- foreign artifact
- Warm-Start 异族痕迹
verified: '2026-11-11'
verified_at: '2026-11-11T21:41:56.506+08:00'
source:
  conversation: 22139001-636b-4095-b659-bf173c2ed4f2
---
需求来源：水彩/普通立绘暖启仍可能灌进 App Icon、HUD、合成梯等异族交付物话术；此前只拦带分数的 foreign artifact，无分条目与 habit/keep/知识卡仍漏。
必须保持：
1) 既有 stale_merge / 旧recipe不进生图词 / 花园keep / 冷暖去冲突仍生效；
2) _foreign_artifact_bleed：命中 App Icon/HUD/合成梯等痕迹时，先按 module+goal 同族剥离（merge 剥合成梯词、ui 剥HUD、app_icon 剥图标词），剥离后仍有异族词才判串题；
3) 拦点：habit_relevant、filter_keeps、无强主题时的 soft_goal_overlap（不再要求有分数）、知识卡 _knowledge_ok；
4) 任务自身 goal/module 已含同族痕迹时不误拦；禁令句「禁止做成主菜单」不因含主菜单词被强主题路径误丢（强主题仍走 entry_topics−ctx）。
入口：improve/warm_start.py → build_warm_start_pack。
适用：所有 converge 暖启注入。
