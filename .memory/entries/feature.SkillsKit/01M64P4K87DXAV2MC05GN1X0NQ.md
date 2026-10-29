---
id: 01M64P4K87DXAV2MC05GN1X0NQ
module: feature.SkillsKit
entity: LowPoseLock
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/scoring.py#audit_score_inflation
- skills_kit/prompt_scale.py#SCALE_DIM_LOCK_LEVELS
revision: git:3e9eae9
author: yanghu
note_date: '2026-10-30'
summary: draw变弱主因错解构+红线漏拦，不是无瑕疵25%
verify: 对照 regen3-c02-low.json 的 ref_analysis 与 ref.jpg；audit 对软措辞压≤8.50
applies: 解释展陈重跑后 draw 变弱/像/姿势漂
aliases:
- 无瑕疵25%
- 前三个相似度
- 姿势没锁住
source:
  conversation: ad2110dc-14c1-4866-a441-1909136ea8d1
---
regen3 前三案例观感「弱且像」与案例02 low姿势漂，主因不是无瑕疵占官方分25%。
证据：旧 hp_dm 同权重已到9.5+；无瑕疵从25%降到15%在 craft9.5/flaw8.5 时只抬约0.1分。
两套75%勿混：①官方分五维工艺合计75%；②画家锁表 low 光影锁定强度75%。提高无瑕疵占比只会更难爬分。
真实根因：
  ①c02 ref_analysis 误写「双手撑地微后仰」（参考实为搭膝），四轮锁错DNA导致档间极相似；
  ②动作红线原先词表过窄，缺陷已写「姿态锁不稳/偏离参考侧收腿」仍可9.12；
  ③c01 low/med/high 机位几乎同框、高档未真正跃升，分数8.6~8.8弱于旧9.54。
