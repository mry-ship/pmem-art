---
id: 01M708NWN7D1RSHYFVSW8H049H
module: feature.SkillsKit.Converge
entity: SkillPolish20261109
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-09'
summary: 技能打磨：暖启过滤+水彩benchmark+早停可关文案+降级菜单
verify: python3 -m unittest tests.test_warm_start_guardrails -q；python3 pmem_art.py
  skills --verify --quick；benchmark lookup 水彩
applies: 改 warm-start/benchmark/agent_router/skill_specs 后
---
需求：在保证流程/效果可验证变好的前提下做技能侧优化（不做赌画质空改）。
必须保持：到线≥9.5、route 闸、WARM_START 仍自动并入。
入口：见 Improve/WarmStartGuardrails 新条；skills --install 已刷新十技能。
