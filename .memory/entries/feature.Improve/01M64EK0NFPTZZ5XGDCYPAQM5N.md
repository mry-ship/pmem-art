---
id: 01M64EK0NFPTZZ5XGDCYPAQM5N
module: feature.Improve
entity: ReflectionThreshold
kind: feature
status: active
supersedes: []
anchors:
- improve/reflection.py
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: finish写反思时会话缺阈值则回退9.5，不得默认旧9.6
verify: python3 -c "import inspect,improve.reflection as r; assert '9.5' in inspect.getsource(r)"
applies: converge finish 后写反思 / 静默进化读取会话阈值时
aliases:
- 反思阈值
- accept_threshold
source:
  conversation: 3551449c-c43f-4703-8575-43749b09f5ba
---
需求来源：停机线改为 9.5 后，converge finish 写入反思包若会话没有 accept_threshold/threshold，旧回退 9.6 会把「是否达标」记错，污染后续教练与静默进化信号。
必须保持：improve 侧从会话读停机线时，缺省回退为 9.5，与 DEFAULT_THRESHOLD / ConvergeGate 一致；
不因此改 AutoAccept（仍禁止自动 accept --all）或 SharedKnowledge 上浮规则。
入口：improve/reflection.py 组装反思字段时的 threshold 回退。
