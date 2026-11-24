---
id: 01M866RH3CVWC3VPDWSCKGSN4G
module: feature.SkillsKit.Converge
entity: HurdleBoundStop
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge_policy.py#decide_round_stop
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 门槛仍压着正式分时，第2轮停，不再开第3轮
verify: unittest tests.test_converge_guards.TestPolicyDefaults.test_hurdle_bound_stops_at_round_2
  -q
applies: safe_early_stop 开启，UI 或图标的门槛维仍低于线
aliases:
- 20分钟
- STOP_HURDLE_BOUND
source:
  kind: conversation
---
需求来源：一次桌面图标跑满 3 轮、墙钟 20 分钟。安全区低于 8 时正式分被改成该维，7.2 涨到 7.6 再涨到 7.9，平台早停不触发，第 3 轮到不了 9.5。
必须保持：safe_early_stop 开启时，第 1 轮门槛未过仍可修一轮。
从第 2 轮起，正式分仍被门槛维压住且低于达标线，judge 返回 STOP_HURDLE_BOUND，ready_to_finish，不再开下一轮。
掉分仍先记 STOP_REGRESSION。
9.5 不降，审图不跳过。
适用：UI / 图标等带门槛维的审图，且项目开了 safe_early_stop。
入口：skills_kit/converge_policy.py 的 decide_round_stop。
