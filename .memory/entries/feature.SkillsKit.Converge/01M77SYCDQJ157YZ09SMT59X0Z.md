---
id: 01M77SYCDQJ157YZ09SMT59X0Z
module: feature.SkillsKit.Converge
entity: PromptDriftGuards
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/must_fix.py#sanitize_continuation_fix
- skills_kit/final_prompt_gate.py
- skills_kit/prior_reuse_gate.py
- skills_kit/converge.py
revision: git:2b2e16d
author: 1002378395@qq.com
note_date: '2026-11-12'
summary: 续写剥换轨句+L1锁钉+最终Prompt对账+generate拒旧交付
verify: unittest tests.test_must_fix tests.test_final_prompt_gate tests.test_prior_reuse_gate
  -q
applies: converge generate / judge next_fix 续写与出图 description 对账时
source:
  conversation: b184581b-9d2c-4d9d-9f09-b09811f9f431
---
需求来源：提示词方向漂移审计（R2+改点换轨、另写brief、generate静默垫旧skill资产）。
必须保持：
1) must_fix.sanitize_continuation_fix 剥换题材/换画风/换技能/推倒重来后再 clip/inject；
2) compose_continuation_prompt 钉 L1 locks 并写「禁止借改点换题材」；
3) generate 打印 FINAL_PROMPT_SHA1 + final_prompt_gate.assert_used_final_prompt；回合写入 final_prompt_sha1；
4) generate 与 start 同样跑 assert_no_silent_prior_asset_reuse（扩 sheet_r / .memory-art/converge / RECIPE）；写实漂移词含光泽卡通3D。
适用：所有 converge generate R2+ 与出图对账。
入口：skills_kit/must_fix.py、prompt_scale.compose_continuation_prompt、final_prompt_gate、prior_reuse_gate、converge generate。
