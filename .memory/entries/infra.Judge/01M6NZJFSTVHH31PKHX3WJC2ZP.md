---
id: 01M6NZJFSTVHH31PKHX3WJC2ZP
module: infra.Judge
entity: VisualEvidenceRerate
kind: feature
status: active
supersedes: []
anchors:
- vlm_judge.py#build_judge_system_prompt
- vlm_judge.py#maybe_run_independent_vlm_judge
- vlm_judge.py#_merge_vlm_reviews
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: VLM按像素记录六维证据，临界分只自动复评一次
verify: git diff --check；pyw -3 -u -m unittest tests.test_vlm_judge -v（本环境提示 No suitable
  Python runtime found，测试未执行）
applies: converge judge 使用独立 VLM 且图片可读取时
aliases:
- 自动复评
- 评分证据
- VLM临界复核
source:
  conversation: 01a1abb8-0adc-7403-bf8c-04a43e507842
---
需求来源：用户要求评分自动化、无需人工确认，并在第三方 VLM 可用时增加评审上下文隔离、评分证据和临界自动复评；
VLM 未配置时仍保留 Agent 自评。
独立 VLM 请求只发送当前图片、任务简述和评分档位，不发送生成 Prompt 或首评分数。
模型输出六维像素证据并写入 sidecar/评分结果。
官方加权调和分距目标线不超过 0.25，或解析到硬门槛冲突时，当前图片再独立评一次；
按维度均值合并，两次意见和分差保留；
一位小数均值采用十进制四舍五入。
复评失败保留有效首评。
既有六维加权调和分、反虚高审计、9.5 停机线和物理/解剖硬闸行为保持。
