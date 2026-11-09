---
id: 01M70S6MGKZ17EBSXB41S2X32E
module: feature.SkillsKit.Router
entity: RouteAuditFix20261110
kind: correction
status: active
supersedes: []
anchors: []
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 修合成梯/别画背景/锁风验证/概念图误伤与种闸绕过
verify: python3 -m unittest tests.test_route_false_fire tests.test_route_advise tests.test_agent_route_stability
  -q
applies: 改 agent_router / route_gate / route_bank / 路由测例时
---
审计修复（含找漏两轮）：
1) _wants_merge：裸整表/越来越大须长语境；禁止没有合成梯时靠八档硬开；去掉一档/overview/ladder 误点亮。
2) 别画背景与不画背景同样豁免审图。
3) 锁完出图等串 style→clone；裸验证图当题材不串；以后都用这张生图只锁风。
4) 裸概念图→普通图；一套图标→icon_unspecified。
5) named seed：stop 拒绝；named_id 必须∈ plan.route_ids。
6) advise：近邻冲突 medium→low；非展陈≥3 支 ask；clear_merge 去掉越升越大。
7) colloquial：删除越升越大→合成梯 rewrite/近邻扩展。
8) agent_route_cases 对齐 JOB_REMAP/ASK。
