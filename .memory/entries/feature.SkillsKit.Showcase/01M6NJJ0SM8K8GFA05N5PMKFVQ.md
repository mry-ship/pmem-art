---
id: 01M6NJJ0SM8K8GFA05N5PMKFVQ
module: feature.SkillsKit.Showcase
entity: ShowcaseGateProcessBoard
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_wants_merge
- skills_kit/showcase_gate.py#audit_showcase_html
revision: git:28ae4ac
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 复核Fix1-5：merge词路由、无win过程板闸、night_city样张
verify: pyw -3 -u -m unittest tests.test_showcase_gate tests.test_agent_route_stability
  tests.test_process_board -q
applies: 复核审计修复后的回归
---
复核 Fix1–5 时又修了三处：
1) agent_router._wants_merge 补交付/链型词（shop_ladder/overview/per_cell/整表/逐格等），避免新用例被判普通图；agent_route_cases 文案加「合成梯」锚点。
2) showcase_gate：过程板无 win 时只审最高分卡（同分取更大轮次），用页上最大轮次作完成轮，避免无 win 整页误放行。
3) 补齐测试样张 docs/showcase/default_round/images/night_city_ref.png 与 comparison/scale_01_night_city_high.jpg。

验证：unittest showcase_gate / agent_route_stability / process_board / route_* / reasonableness / skill_router / GateFixes 共 165 项 OK；
boards 30 中仅 instrument-rebuild-5x3（9.42/3轮）正确 FAIL；
section_cut_ok=true。
