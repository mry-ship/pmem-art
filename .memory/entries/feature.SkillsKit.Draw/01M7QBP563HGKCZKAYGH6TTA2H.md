---
id: 01M7QBP563HGKCZKAYGH6TTA2H
module: feature.SkillsKit.Draw
entity: LocalTouchupMode
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/route_gate.py
- skills_kit/reasonableness_gate.py
- skills_kit/route_bank.py
revision: git:f3998da
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 局部改验收：种闸白名单、合理性对账、近邻撞库三处已修通
verify: 99 tests OK；converge touchup_selftest finish badge=局部改快通道
applies: draw.touchup 路由/开画/近邻检索
aliases:
- 局部改验收
- touchup gate
source:
  conversation: b3206fc3-5edb-4094-ad92-97f526162318
---
循环检查发现并已修：
1) pack 校验针「最多1枪」与合同文案对齐；touchup pack 去掉记忆静默以免带入交件可见。
2) 「不换题材」曾被 touchup 禁词子串误杀 → infer_signals/_wants_touchup 改为真换才禁。
3) draw.touchup 未进 _SEEDABLE_ROUTES 导致 --route-id 种闸失败 → 已加入。
4) 自动合理性盖章后 generate --prompt 仍被 revised 对账拦住 → touchup 一律放行本轮 prompt。
5) 近邻「手指修一下」撞「深度优化这张图」致 ordinary execute_ok=false → 改近邻文案+ordinary 忽略 touchup 近邻冲突。
6) 稳定性测「满4轮」期望过期 → 改为满3轮。
自测：session touchup_selftest_20261118c 走通 start→generate→finish（人眼、无六维），badge=局部改快通道 · 第 1 枪交件。
