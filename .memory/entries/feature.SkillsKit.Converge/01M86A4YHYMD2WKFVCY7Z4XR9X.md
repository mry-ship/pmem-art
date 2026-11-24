---
id: 01M86A4YHYMD2WKFVCY7Z4XR9X
module: feature.SkillsKit.Converge
entity: JudgeWritesNextPrompt
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 审图继续时同一次写好下一轮定稿，登记不再组装
verify: python -m unittest tests.test_converge_emit_prompt.TestConvergeEmitPrompt.test_judge_writes_next_prompt_once
  -q
applies: converge judge 未达标且 should_continue 为真时
source:
  conversation: 1f7af752-c811-4865-9341-233eb6ffe881
---
需求来源：画师要求所有技能少等上一段脚本、少重算一遍提示词，且不降生图质量。
必须保持：审图未达标且还要下一轮时，同一次进程把分数写进会话后，用和单独 emit 相同的装配写好下一轮 pending_final_prompt（只组装一次）。
登记成图仍复用该定稿，不再跑合理性、Warm-Start 和装配。
达标或安全早停不写下一轮。
分数和定稿以会话 JSON 为准，不等外层脚本把日志一次性写完。
9.5、审图、合理性、最多 3 轮都不改。
适用：所有走 converge judge 的技能。
入口：converge judge；继续时打印 SCORE_READY 和下一轮最终 Prompt。
