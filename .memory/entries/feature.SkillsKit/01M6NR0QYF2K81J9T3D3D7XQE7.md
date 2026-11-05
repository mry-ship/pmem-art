---
id: 01M6NR0QYF2K81J9T3D3D7XQE7
module: feature.SkillsKit
entity: SkillSlicePackGap
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_registry.py#slice_route_body
- skills_kit/skill_registry.py#_draw_pack_headings
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 出图/图标执行包已打包闭环与清单
verify: unittest tests.test_skill_router；slice_route_body(draw.clone) 含 reasonableness
applies: 总控按 registry 交执行包给子 agent 时
aliases:
- 裁节缺口
- 合同打包
---
已落地：registry 增加 pack_headings + slice_route_body；
draw.clone/variant/multi/key/ordinary 打包零点五+第二节(+合同)+记忆静默；
icon Mode 打包 Mode+### Mode 清单+记忆静默；
section_cut 与 test_skill_router 断言 clone 包含 reasonableness。
draw 改为先 route 禁先自判；
agent 交执行包并加双参考降级话术；
prompt Step0 跑 route 且方案标 route_id；
lens-propose 改 stub；
skills --list 对 description 做 rewrite_cli；
docs/COMMERCIAL_BENCHMARK.md 短表。
验证：unittest tests.test_skill_router tests.test_route_advise OK；
skills --install。
