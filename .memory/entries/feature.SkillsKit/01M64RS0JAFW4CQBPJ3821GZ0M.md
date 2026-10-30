---
id: 01M64RS0JAFW4CQBPJ3821GZ0M
module: feature.SkillsKit
entity: SoftInflationCap
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#audit_score_inflation
- skills_kit/skill_specs.py
- skills_kit/converge_policy.py
revision: git:7101334
author: yanghu
note_date: '2026-10-30'
summary: 软质量短板词再硬顶≤8.90；媒介豁免与否定不误杀
verify: python3 -m unittest tests.test_param_validation.TestGateFixes.test_soft_quality_shortfall_hard_caps_at_890
  tests.test_converge_guards.TestJudgeAnatomyVeto.test_flat_light_keyword_does_not_cap_pixel
  -q
applies: converge judge / Absolute-5D 自评与独立 VLM 共用的反虚高校准
aliases:
- 反虚高
- 软质量虚高
- 8.90硬顶
- 平光封顶
source:
  conversation: ce0a2f88-0981-43b7-8c37-34c2ca7e87a4
---
需求来源：软质量虚高闸曾收窄到只认画幅比例，缺陷写平光/呆板/照搬等仍可报 9.5；恢复软质量硬顶。
必须保持：缺陷含平光、呆板、照搬、贴原、证件照、缺乏飞白/飞白不够/不见飞白、颗粒太均匀、数字化噪点|痕迹|滤镜（及英文 flat light / copy the reference）且校准分>9.0 时，audit_score_inflation 硬顶 ≤8.90；
裸词「数字化」不封顶；
STYLE_INFLATION_IGNORE 对 pixel/flat/wash/graphic 豁免其合法词；
否定句与「已解决」不误杀；
解剖/姿态硬伤闸门不变。
入口：skills_kit/scoring.py#audit_score_inflation；
skill_specs /pmem-draw 文案；
tests.test_param_validation.TestGateFixes.test_soft_quality_shortfall_hard_caps_at_890。
