---
id: 01M6KVQKHZQMYZB0R78BFD93A9
module: feature.SkillsKit
entity: ReasonablenessGate
kind: feature
status: active
supersedes:
- 01M6DYYM99FPEB5X13QR10BK76
anchors:
- skills_kit/reasonableness_gate.py#_heuristic_issues
- skills_kit/merge_relation.py#judge_relation_rows
- skills_kit/converge_policy.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 合理性闸补 UI 禁叙事垫图/IconA 满幅/split 状态机/软糖介质/合成梯母体
verify: python3 -m pytest tests/test_reasonableness_gate.py tests/test_merge_relation.py
  tests/test_converge_guards.py tests/test_v8_skill_converge_reflow.py -q
applies: 跑 /pmem-draw /pmem-ui /pmem-icon /pmem-merge-ladder 或任意 converge generate
  / relation-judge 时
aliases:
- 合理性闸
- reasonableness
- UI垫图
- 软糖介质
- 满幅直角
---
需求来源：skill_full_run_1105 电池反向分析。必须保持：
  1) ui 禁叙事/气氛/立绘/茶会裁切当垫图母版（口语扩覆盖）+控件工艺+CTA避脸。
  2) icon.a 满幅直角；
圆角底板肯定句拦，否定/一眼失败用 _negated_before（不含裸无/非，避免无字漏拦）。
  3) split 开盖须铰链/解锁；
STATE_BAD 不跨句误杀禁止闭锁开盖。
  4) 软糖在 ordinary/icon.c/shotpack/clone/variant/merge 锁软介质。
  5) merge same_object 须显式保留母体句；
礼盒/奖杯换货主语由 merge_relation 拦（无CJK \b）。
  6) 掉分早停默认 0.15 / min_round=2。
入口：reasonableness_gate/merge_relation/converge_policy/skill_specs。
