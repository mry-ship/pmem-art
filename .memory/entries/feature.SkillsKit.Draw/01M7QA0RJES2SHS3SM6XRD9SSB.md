---
id: 01M7QA0RJES2SHS3SM6XRD9SSB
module: feature.SkillsKit.Draw
entity: LocalTouchupMode
kind: plan
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#JOB_REMAP
- skills_kit/understanding_contract.py#classify_feedback
- skills_kit/prompt_scale.py
revision: git:f3998da
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 规划：成图后局部修改走快改通道，不重跑完整三轮闭环
verify: 玩家确认方案后实现；实现后「局部修」应不再默认 max_rounds=3 / medium
applies: 玩家对已有成图做局部瑕疵/小改，且不换题材机位身份时
aliases:
- 局部修改
- 局部调整
- 局部修
- 快改
- touchup
- spot fix
source:
  conversation: b3206fc3-5edb-4094-ad92-97f526162318
---
需求来源：玩家反馈小瑕疵/局部改若再走 route→技能→最多3轮 converge 太慢；希望指出部位文字改，或垫局部参考图+文字。
现状：JOB_REMAP 已把「局部修/只改手」映射到 draw.ordinary 并 note scale=low，合同 L2 也认「修一下/微调」；但步骤 note 仍写 medium+最多3轮到线，实际仍是完整闭环，墙钟没省下来。
规划方向（待玩家确认后再实现）：优先「快改通道」而非新长大技能——入口口语/斜杠点名；
硬闸只改局部、锁机位身份题材；
垫待改成图（可加局部参考）；
默认 1 枪出图、可选 0～1 次看图验收、不到线不强制凑轮；
记忆用 feedback 轻量记，不强制写满 converge 履历。
排除：不要把局部修伪装成普通三轮合同交差；
不要一上来做真 mask inpaint（Cursor GenerateImage 无区域 mask）。
