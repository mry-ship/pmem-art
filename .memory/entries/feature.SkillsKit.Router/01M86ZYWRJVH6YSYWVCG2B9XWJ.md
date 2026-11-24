---
id: 01M86ZYWRJVH6YSYWVCG2B9XWJ
module: feature.SkillsKit.Router
entity: ExpressionKeepFalseClone
kind: risk
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_expression_swap_locked
- skills_kit/agent_router.py#_new_subject
- skills_kit/agent_router.py#_wants_touchup
revision: git:ff5f930
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 表情句后接保持且带图时，会先判成克隆
verify: 带图 plan_route 该句 route_ids 含 draw.clone；无图则为 draw.variant
applies: 同一身份改表情且要求其余保持，并带着原图走 route 时
aliases:
- False Execute
- 表情保持误克隆
source:
  conversation: 7f9cd1bd-0998-40af-b6c9-8c432eb321b3
---
现象：带原图说「把这只猫改成惊讶的表情，其他保持不动」，route 会选 draw.clone 并可以 execute_ok。没附图时同一句走 draw.variant，也不进局部改。
原因：表情锁要求改成/换成+表情词贴在句末；「其他保持不动」接在后面就锁失效。「保持不动」不在局部改保持词里，局部改不命中。「改成」仍算换题材，而克隆分支写在变体分支前面。冲突闸只比较原话规则和标准句；标准句若跟错判一致，不会拦。
影响：错技能会直接开一次生成。这是 False Execute，比多问一句贵。
别怎么做：不要靠再写一条标准句把这次错判确认下来；带图且句尾还有保持要求时，先问是局部改还是变体，不要直接开克隆。
