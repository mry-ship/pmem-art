---
id: 01M7MS4DT6GQH620SZR1MD6GHS
module: feature.SkillsKit.Converge
entity: DoctorHookBoundary
kind: decision
status: active
supersedes: []
anchors:
- lifecycle.py#DOCTOR_HOOK_EVENTS
- lifecycle.py#maybe_lazy_doctor_on_hook
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: lazy doctor 只在 session/stop/finish 抢槽，出图中途不 spawn
verify: unittest tests.test_lazy_doctor.TestLazyDoctorHooks -v
applies: 装了 pmem-art hooks 的仓库；日常 converge 出图中
aliases:
- 出图中途禁doctor
- 禁中途体检
---
现象：pre-gen/post-asset 等出图中途 hook 也会抢 lazy doctor，与「主链禁体检」冲突，白烧墙钟。
决定：DOCTOR_HOOK_EVENTS 收窄为 session、stop、converge_finish；中途事件只消费已写 tip、不 spawn。
排除：不为了省时间下调 9.5 门槛或取消六维裁判。
