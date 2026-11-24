---
id: 01M84FGTT9SKK3JSC3YWS451W5
module: feature.SkillsKit.Converge
entity: DeliverySpeedPrepare
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#cmd_converge_prepare
- skills_kit/icon_geometry.py#icon_geometry_skip_reason
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: 出图准备并进程，过期槽不占位，图标过小跳过远程审图
verify: pyw -3 -u -m unittest tests.test_delivery_speed tests.test_converge_emit_prompt
  tests.test_hard_pits_gates tests.test_reasonableness_gate tests.test_converge_guards
  -q
applies: 日常出图准备与 Mode A 从零新画；不降低 9.5
source:
  kind: test
---
需求来源：缩短出图准备，不降低 9.5。
必须保持的行为：
1) `converge prepare` 在同一进程完成 start、合同、合理性、emit-prompt。合理性没过时不建会话、不占并行槽。Warm-start 在合同和修订句落定后只装一次。
2) 合格线仍是 9.5，最多 3 轮。prepare 不代替 judge，也不登记成图。
3) 超过 agent.slot_stale_hours（默认 36，0 为关闭）仍未 finish 的会话不占槽，不改 JSON。
4) 只有目标写了图标身份，且符号跨度明显低于 62% 时，才跳过远程审图，正式分不超过 7.2。单独写 1024 不当成图标。
5) 图标和界面不注入狗、虹膜、全身/半身，除非目标自己点了这些词。口语 appicon 进入 icon.a。从零新画示例用 medium。
适用条件：日常出图准备，以及 Mode A 从零新画。
入口：pmem_art.py converge prepare；skills_kit/parallel_slots.py；skills_kit/icon_geometry.py；improve/warm_start.py。
