---
id: 01M7MS41MQQSEY0WWS1JN4F384
module: feature.SkillsKit.Agent
entity: DeliveryWallClock
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/install.py#_render_agent_doc_block
- skills_kit/skill_specs.py
- lifecycle.py#DOCTOR_HOOK_EVENTS
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 日常交付墙钟五条：到线停/禁中途体检/禁探测图/确认≤2/首轮brief写准
verify: pmem-art.mdc 与 pmem-agent/pmem-draw SKILL 含「日常交付墙钟」或「墙钟硬规」；unittest tests.test_skill_router
  -q
applies: 日常出图交付（非玩家点名自测/单独维护任务）
aliases:
- 墙钟
- 加快流程
- 确认不超过两次
source:
  conversation: 7756ad1a-6c4d-4c92-a613-772055b4f6be
---
需求来源：玩家反馈闭环墙钟过长，勾选不伤结果的加速项（不含平台期早停）。
必须保持：
1) ≥9.5 到线即停，禁止凑满轮次；
2) start→generate→judge 主链禁止 doctor/hygiene/深检，只允许出图前、finish 后或单独点名维护；
3) 日常交付禁止 Probe/Overwrite/额外探测再生图，自测不得混进交付会话；
4) 硬不确定确认 ≤2 次且一次问清，可默认项直接默认；
5) 首轮 reasonableness revised 一次写准身份/机位/材质/禁令/底色。
入口：总规则「日常交付墙钟」；pmem-agent「审完怎么走」+墙钟节；pmem-draw Step1 墙钟硬规。
