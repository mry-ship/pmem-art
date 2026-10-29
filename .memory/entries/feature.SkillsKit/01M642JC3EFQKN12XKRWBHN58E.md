---
id: 01M642JC3EFQKN12XKRWBHN58E
module: feature.SkillsKit
entity: RecomposeEvidence
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/prompt_scale.py#_recompose_change_evidence
- skills_kit/skill_registry.py#_mode_heading
- skills_kit/absolute_5d_agent_rubric.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 提示词里的重构机位和上一轮成图都不算换了机位，缺陷禁止抄上一轮
scope: project
verify: python pmem_art.py check-scale-gates --self-check；正文含没换机位时不得判已换机位
applies: high/recompose 档与图标Mode标题解析
aliases:
- 垫图
- 抄缺陷
- Mode标题
---
试过把「提示词写了重构机位」或上一轮成图当作已经换机位的证据，会让 recompose 在没换机位时停机，high 也会把贴原当抬档。
排除：_recompose_change_evidence 只认看图写的机位证据；
正文出现「没换机位 / still the original」一律不算换了。
禁止把上一轮 defects 原句贴到本轮。
recompose 缺陷第一句必须回答仰或俯、人占画面大约多少、主光是窗火还是灯笼。
high 必须写明相对原图多出来的那一处光影或叙事，写不出来就把构图当贴原打。
图标 Mode A/B/C 的标题要从专属 Mode 节取，不要命中 Step 5 闭环标题。
