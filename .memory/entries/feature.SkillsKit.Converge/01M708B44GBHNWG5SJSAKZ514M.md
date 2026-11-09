---
id: 01M708B44GBHNWG5SJSAKZ514M
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: decision
status: active
supersedes: []
anchors:
- skills_kit/converge_policy.py#decide_round_stop
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: 临时屏蔽安全早停：config.safe_early_stop=false
verify: 'decide_round_stop(..., safe_early_stop=False) 不返回 STOP_REGRESSION；.memory-art/config.yaml
  converge.safe_early_stop: false'
applies: 想先跑满轮次追最高分、暂时不要掉分早停时
---
取舍：玩家要先追最好效果图，担心一次掉分切掉回升机会。
方案：不删 0.15/R2 默认与 STOP_REGRESSION 逻辑；
新增 converge.safe_early_stop（代码默认 True），项目 config 临时设 false 屏蔽掉分/平台早停；
≥9.5 到线停与 max_rounds 仍生效。
恢复：把 .memory-art/config.yaml 的 safe_early_stop 改回 true（或删键用默认）。
