---
id: 01M64P5HTPHVWK360VF6NASRR3
module: feature.SkillsKit
entity: LowPoseLockGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#audit_score_inflation
- skills_kit/medium_family.py#apply_family_to_profile
- skills_kit/absolute_5d_agent_rubric.py#agent_absolute_5d_judge_prompt
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: low姿态漂移软措辞fail-closed；解构与directive锁落点
verify: python3 -m unittest tests.test_param_validation.TestGateFixes.test_low_soft_pose_drift_phrases_hard_cap
  -q；get_converge_scale_profile('low') directive 含姿态落点
applies: low档有参考的人物收敛
aliases:
- 姿势没锁住
- 搭膝改撑地
- 姿态锁不稳
source:
  conversation: ad2110dc-14c1-4866-a441-1909136ea8d1
---
需求来源：regen3 案例02 low 姿势相对参考漂成撑地，且画师怀疑无瑕疵25%。
必须保持：
1) allow_action_pose_change=False 时，缺陷出现「姿态锁不稳」或「偏离/相对参考+手腿膝姿」等软措辞也压分≤8.50；否定句「未改动作」不误伤。
2) Step0 解构与 skill 清单必写左右手脚落点；low 的 Absolute-5D 裁判提示对照参考像素落点。
3) medium_family 覆写 prompt_directive 后仍追加「锁姿态落点…禁止搭膝改撑地」。
官方分仍是工艺75%+无瑕疵25%，本改不动该比例。
入口：scoring.audit_score_inflation；absolute_5d_agent_rubric；medium_family.apply_family_to_profile；/pmem-draw Step0。
