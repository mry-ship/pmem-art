---
id: 01M64FG7Z2EAC2CD5N4DEMYH29
module: feature.SkillsKit
entity: AgentRoute
kind: decision
status: active
supersedes: []
anchors:
- skills_kit/route_bank.py#distill_entries
- skills_kit/route_bank.py#retrieve
revision: git:fe6a96b
author: yanghu
note_date: '2026-10-30'
summary: 路由预训用蒸馏+本地检索，不灌两万条进LLM上下文
scope: project
verify: advise_route 的 llm_hints.neighbors≤5；distill_entries 长度 < 全量 cases
applies: pmem-art 路由预训与话术库演进
aliases:
- 预训记忆
- 相似度筛选
source:
  conversation: cb47efd7-68ce-4970-9af1-8ef2b26869b1
---
取舍：不把 2 万条话术原文灌进大模型；从 2500+ 组合用例蒸馏难例全留+每路由原型上限，本地字符 n-gram 检索 top-k，再交给规则 plan_route；LLM 只看小包校准。
排除：为「准确率」把整库或近重复话术贴进 Agent 上下文。
用户扩技能：注册表 when/phase + user.jsonl 正负例 + 回归门禁；禁止教练式静默全收路由语料。
