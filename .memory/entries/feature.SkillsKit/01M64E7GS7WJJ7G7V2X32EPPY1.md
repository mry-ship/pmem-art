---
id: 01M64E7GS7WJJ7G7V2X32EPPY1
module: feature.SkillsKit
entity: ConvergeGate
kind: feature
status: active
supersedes:
- 01M642JB2BYSMW32V9PS3W80PH
anchors:
- skills_kit/prompt_scale.py
- skills_kit/showcase_gate.py
- skills_kit/skill_specs.py
- pmem_art.py
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 不到9.5或满4轮不能当终稿，每轮只垫最初参考图，展陈页要过showcase-gate
verify: python3 -c "from skills_kit.prompt_scale import DEFAULT_THRESHOLD; assert
  DEFAULT_THRESHOLD==9.5"；python pmem_art.py showcase-gate 对未满轮且<9.5的格拒绝
applies: 生图闭环、图标Mode A/C关键枚、合成梯、带评分格的展陈HTML
aliases:
- 停机线
- 合格线
- '9.5'
- 阈值
source:
  conversation: 3551449c-c43f-4703-8575-43749b09f5ba
---
需求来源：停机线 9.6 与档位锚「9.5=优」错位，实测会话最高分达标率约 1.6%、71% 卡在 9.4–9.6，闭环退化成固定跑满 4 轮。用户 2026-10-30 要求改停机分，选定 9.5（不用 9.45）。
必须保持：生图闭环（含图标 Mode A/C 关键枚）不到 9.5 就要再出，满 4 轮才取最高分；未 judge 不能开下一轮，finish 在未达标且未满轮时失败。
每一轮只垫最初参考图（high/recompose 已换机位证据时按 PadChangedCamera），修正只写进提示词。
展陈 HTML 收页前必须 showcase-gate 通过：有格 <9.5 且未满 4 轮不能交。
DEFAULT_THRESHOLD、四档 target_score_threshold、config target_thresholds、skill 合同与 CLI --threshold 默认均为 9.5。
入口：skills_kit/prompt_scale.py DEFAULT_THRESHOLD；
skills_kit/showcase_gate.py；
skills_kit/skill_specs.py；
.memory-art/config.yaml converge.target_thresholds。
