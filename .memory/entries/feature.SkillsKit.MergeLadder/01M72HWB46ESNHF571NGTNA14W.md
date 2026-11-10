---
id: 01M72HWB46ESNHF571NGTNA14W
module: feature.SkillsKit.MergeLadder
entity: ConvergeRouteGateRace
kind: risk
status: active
supersedes: []
anchors:
- pmem_art.py
revision: git:a898187
author: 1002378395@qq.com
note_date: '2026-11-10'
summary: 并行多链 converge start 会抢共享 last-route 闸
verify: 并行开三链时观察 converge start 是否报「上次 route 原文与当前 goal 对不上」
applies: 同一仓库并行开多个 merge converge session 时
source:
  conversation: 198400ce-a2af-48b4-8bfd-5c6eabf5c2c3
---
三张合成梯并行重画时，各自 pyw route 会覆盖全局上次 route 原文；
后开的 converge start 若 goal 不含当前 last-route 锚点就被闸门挡住（管乐 start 曾被浇水/果酱 route 原文挡住）。
影响：并行 session 启动失败或互相踩线。
规避：每条链 start 前立刻 route，goal 必须包含刚写出的 route 原文锚点；或串行 start 后再并行 generate。
