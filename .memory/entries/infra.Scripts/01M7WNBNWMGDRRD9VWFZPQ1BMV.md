---
id: 01M7WNBNWMGDRRD9VWFZPQ1BMV
module: infra.Scripts
entity: NotContract
kind: correction
status: active
supersedes:
- 01M7WNBB7EPRBVMYY10Y24SYHQ
anchors:
- docs/BENCHMARK_LAYERS.md
- skills_kit
revision: git:55fd2ca
author: 1002378395@qq.com
note_date: '2026-11-20'
summary: 批跑非skill合同仍成立；与B1非视觉证并列
verify: 两条 exclusion 文案均在 wiki/检索可见且互不否定
applies: 改闭环合同或引用benchmark结果时
source:
  conversation: c8eef2a3-73d7-46b8-850d-eeac1e85ee27
---
误操作：NotVisualProof 写入时 supersedes 了 NotContract。
更正：两条排除项同时成立、互不替代——
1) NotContract：改停机/垫图/合成梯合同以 skills_kit 为准，勿只改 scripts/benchmark；
2) NotVisualProof：evolution 剧本分禁止当视觉进化证据。
NotContract 未被推翻。
