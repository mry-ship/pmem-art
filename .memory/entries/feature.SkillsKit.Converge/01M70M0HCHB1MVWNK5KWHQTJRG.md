---
id: 01M70M0HCHB1MVWNK5KWHQTJRG
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: correction
status: active
supersedes:
- 01M708B44GBHNWG5SJSAKZ514M
anchors:
- skills_kit/converge_policy.py#decide_round_stop
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 恢复安全早停：config.safe_early_stop=true
verify: grep safe_early_stop .memory-art/config.yaml 含 true
applies: 日常 converge；不要空烧平台轮
---
旧决定（01M708B44GBHNWG5SJSAKZ514M）临时屏蔽掉分/平台早停追满分，导致展陈并发几乎全员空烧满 4 轮。
现恢复：.memory-art/config.yaml converge.safe_early_stop: true，max_rounds: 4。
逻辑仍在 decide_round_stop；
要再追满轮可临时改回 false。
