---
id: 01M706MP4YRKD220N6PW9TZV7X
module: feature.SkillsKit.Converge
entity: SkillHardening20261109
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/gate_skip.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: 闸门分级·remap·执行卡·benchmark·verify
verify: python3 pmem_art.py skills --verify
applies: 改 route/converge/技能执行包/闸门后
---
落地 gate_skip、warm_start_merged、JOB_REMAP/ASK、执行卡瘦包、benchmark 卡库与垫图双闸、validate_canonical、skills --verify（含 hardening 与安装一致性）。
