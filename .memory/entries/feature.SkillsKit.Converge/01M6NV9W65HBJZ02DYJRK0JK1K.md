---
id: 01M6NV9W65HBJZ02DYJRK0JK1K
module: feature.SkillsKit.Converge
entity: ImageRoundCapShowcaseGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/showcase_gate.py#can_accept_winner
- skills_kit/showcase_gate.py#audit_showcase_html
- skills_kit/converge.py
- skills_kit/process_board.py
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 出图一轮未过线：badge+early@1 过 showcase-gate
verify: py -3 -u -m unittest tests.test_showcase_gate tests.test_process_board tests.test_skill_speed_caps
  tests.test_agent_route_stability -q
applies: single_judge / 出图一轮交件 finish 与过程板闸
---
需求来源：深度审计发现出图一轮（single_judge / max_rounds=1）未过线时 finish 用会话 mr=1 能过，但过程板 HTML 的 showcase-gate 默认 max_rounds=4，胜出格「第 1 轮 · <9.5」无早停字样会 FAIL。
必须保持：
1) can_accept_winner 在 early_safe_stop 时 rounds≥1 即可交（原 ≥2）。
2) finish：single_judge 且未过线 → badge/结论写「出图一轮交件」；过程板 summary 写入 convergence_badge。
3) audit_showcase_html 识别「出图一轮交件|安全早停|STOP_REGRESSION|STOP_PLATEAU」（caption 或页级 summary）。
4) 无 badge 的 1 轮未过线过程板仍 FAIL（预览未结算）。
5) 普通图路由 note 用 ≥9.50（稳定性用例依赖）。
适用：merge overview/per_cell、UI、Icon、split 出图一轮交件；过程板展陈闸。
入口：skills_kit/showcase_gate.py；
skills_kit/converge.py finish；
skills_kit/process_board.py；
skills_kit/agent_router.py ordinary note。
