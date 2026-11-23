---
id: 01M83P9F1WDGA4JH36W4GYKGBH
module: feature.SkillsKit.Converge
entity: ReasonablenessFalsePositive
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_heuristic_issues
- skills_kit/reasonableness_gate.py#_l0_subject_drift
revision: git:dae2c1e
author: 1002378395@qq.com
note_date: '2026-11-23'
summary: UI插画垫否定按字段查；L0改写用二字gram软保留
verify: unittest tests.test_reasonableness_gate.TestReview.test_ui_ban_illust_pad_phrase_not_false_positive
  tests.test_final_prompt_gate.TestReasonablenessL0.test_subject_paraphrase_not_drift
applies: ui/ordinary 合理性闸；R1 revised 含禁令句或同题材改写时
source:
  kind: conversation
---
1) UI _UI_ILLUST_PAD_BAD_RE 原先对 blob 裸 search，「禁止/一眼失败+叙事插画垫」误拦；
   改 finditer+_negated_before，且 draft/revised/notes 分字段查，避免 revised 否定窗口串到 notes 实锤句。
     2) L0 主体锚点对同题材改写（红伞白点蘑菇→红伞蘑菇）误报；
   _l0_anchor_kept 允许≥2 个二字gram命中，且 missing 须过半才判漂移。
