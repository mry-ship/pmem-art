---
id: 01M6GN5JCVC4X390H9TE8A2QM3
module: feature.SkillsKit
entity: DriftResetRule
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/install.py#_render_agent_doc_block
- .cursor/rules/pmem-art.mdc
- tests/test_skill_router.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 跑偏纠偏总规则：扩充口语触发词，并排除局部微调
verify: rg 口语触发 .cursor/rules/pmem-art.mdc；python -m unittest tests.test_skill_router.SkillRouterTests.test_install_keeps_one_command_per_skill
applies: pmem-art init 或 install_skills 写入总规则后
aliases:
- drift_reset
- 跑偏重置
- 条件触发重置
- 口语触发
---
需求来源：多轮对话易沿用旧分析导致纠不回来；
不要常驻写进每个技能前缀。
必须保持：skills_kit/install.py 的 _render_agent_doc_block 含「### 5. 跑偏纠偏」，并列出可识别口语四类——否定翻车（不对/错了/不行/不是这样/理解错了/搞错了/认错了/偏了/跑偏了/跑歪了/离题了/答非所问）、要求重开（重做/重来/推倒重来/另起炉灶/从零再做/重新分析/重新想/不要沿用/别沿用上轮/忘掉上轮/历史作废/刚才那套作废）、要求换路（换条路/换个思路/换方案/别按刚才的做/别微调旧案/不要接着改那版）、路由纠偏（不是这个技能/走错技能了/不该走合成梯图标UI克隆/重新路由）；
另有非口语触发（连续2轮<9.5同病复发；路由被纠正后重走）。
必须保持「不要当成跑偏」清单：就改这一点/把头再小一点/颜色再暖一点/这版留着微调/继续收敛/下一轮按改点修。
当次 brief 带温和重置句，用完即清；
禁止必须换不同路线。
init/install 同步写入 .cursor/rules/pmem-art.mdc、CLAUDE.md、AGENTS.md；
只改本地 mdc 会被覆盖。
仍是规则约束非硬编码扫描。
