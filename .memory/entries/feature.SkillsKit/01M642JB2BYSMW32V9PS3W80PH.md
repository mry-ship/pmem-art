---
id: 01M642JB2BYSMW32V9PS3W80PH
module: feature.SkillsKit
entity: ConvergeGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge_loop.py#loop_followup
- skills_kit/showcase_gate.py#can_accept_winner
- skills_kit/skill_specs.py
revision: git:30ea756
author: 1002378395@qq.com
note_date: '2026-10-29'
summary: 不到 9.5或满4轮不能当终稿，每轮只垫最初参考图，展陈页要过showcase-gate
verify: python pmem_art.py showcase-gate --html <页> 对未满轮且<9.5的格拒绝；未judge时 converge
  generate 下一轮失败
applies: 生图闭环、图标Mode A/C关键枚、合成梯、带评分格的展陈HTML
aliases:
- 停机
- '9.5'
- 垫图
- 展陈闸门
---
需求来源：展陈重跑里 Agent 经常 8.x 就停、把 r1 复制成 final、把上一轮成图垫回去，合成梯又整组刷成同色白模。
必须保持：生图闭环（含图标 Mode A/C 关键枚）不到 9.5 就要再出，满 4 轮才取最高分；
未 judge 不能开下一轮，finish 在未达标且未满轮时失败。
每一轮只垫最初参考图，修正只写进提示词，禁止垫上一轮成图。
展陈 HTML 收页前必须 showcase-gate 通过：有格 < 9.5 且未满 4 轮不能交。
合成梯第一段 3 稿要把 family.type、每件 look、merge_why 说通；
过关后整组 16:9（2x4 相同正方形格）生成再切开交货，组图不是成品。
入口：skills_kit/converge_loop.py 的 loop_followup、skills_kit/showcase_gate.py 的 can_accept_winner、skills_kit/skill_specs.py 的 SKILL_SPECS。
