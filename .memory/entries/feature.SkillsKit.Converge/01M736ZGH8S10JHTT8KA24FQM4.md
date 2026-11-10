---
id: 01M736ZGH8S10JHTT8KA24FQM4
module: feature.SkillsKit.Converge
entity: ConvergeGate
kind: correction
status: active
supersedes:
- 01M6KXJC6M84XSB3WD1CVEW128
- 01M6RDTYJNXPTEW2KYWWD9FKGQ
- 01M726N9ZADQMG2WJ0DAMN5Q5V
anchors:
- skills_kit/converge_policy.py
- skills_kit/showcase_gate.py#can_accept_winner
- skills_kit/converge.py#_split_speed_requested
- skills_kit/validate_params.py#_round_counts_as_passed
- skills_kit/converge_policy.py#decide_round_stop
- .memory-art/config.yaml
revision: git:8ab2d7f
author: 1002378395@qq.com
note_date: '2026-11-11'
summary: 早停默认关；打开仍0.15/R2；multi硬顶与解剖缺维不过关
verify: converge_policy safe_early_stop 默认 false；打开时 drop=0.15 min_round=2
applies: converge decide_round_stop；多图/分态会话；带解剖门的主体
---
现状结论（ConvergeGate 闸门默认）：
1) safe_early_stop 缺省与项目 config 均为关。
   未写成 true 时，掉分与平台不能在第 4 轮前停；
   到线仍 ≥9.5，满 4 轮交最高分。
   若打开早停：掉分 0.15、从第 2 轮起；
   禁止无说明改回 0.5/第 4 轮。
2) 多图一轮硬顶同时认 route_ids / expect_route 的 draw.multi 与 draw.split；
   goal 与 contract 都空、只有 draw.multi 时 _split_speed_requested 为 True，max_rounds 压到 1。
3) 人物/动物/机械/generic 缺 perspective_anatomy 时 _round_counts_as_passed 为 False；
   解剖检查导入或解析抛错也返回 False，不再跳过。
   未写 subject_kind 的旧记录仍按缺陷词与已写维度判断。
曾以为：仓库默认 regression_drop=0.5 / early_stop_min_round=4，或 safe_early_stop 默认开——均已作废。
合并自 3 条更正。
