---
id: 01M6NZJWES8ZDH6AF3HSJC5WB2
module: feature.SkillsKit.Converge
entity: AutomatedScoreEvidence
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/absolute_5d_agent_rubric.py#agent_absolute_5d_judge_prompt
- skills_kit/converge.py#cmd_converge
- skills_kit/converge_judge_bridge.py#score_for_converge
- skills_kit/judge_auto.py#auto_vlm_judge_image
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 自评/第三方评分记录像素证据并自动复核临界分
verify: git diff --check；pyw -3 -u -m unittest tests.test_vlm_judge -v（本环境提示 No suitable
  Python runtime found，测试未执行）
applies: converge generate/judge/finish 评分流程及 converge_judge_bridge
aliases:
- 自评评分证据
- 无人校准
- 临界分复评
source:
  conversation: 01a1abb8-0adc-7403-bf8c-04a43e507842
---
需求来源：用户表示 VLM 经常未配置，由 Agent 自评兜底；
不加人工确认或人工校准。
Agent Absolute-5D 要求 strengths/defects 指向当前图像可见证据，并在调和分距目标线 0.25 内或透视分接近硬门槛时重新看图、按维度均值给出最终分。
独立 VLM 的证据、证据缺项、复评次数和分差随每轮记录并在 converge judge 输出中可见；
converge_judge_bridge 返回结果也保留这些字段。
原有生成与评分分阶段、评分权重、硬闸、停机阈值和无需人工确认行为保持。
