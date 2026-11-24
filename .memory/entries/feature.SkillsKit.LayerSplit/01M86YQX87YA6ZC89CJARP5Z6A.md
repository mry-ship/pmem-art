---
id: 01M86YQX87YA6ZC89CJARP5Z6A
module: feature.SkillsKit.LayerSplit
entity: IsolatePrompt
kind: feature
status: active
supersedes: []
anchors:
- scripts/pmem_layer_split/isolate.py#_slot_tag
- scripts/pmem_layer_split/isolate.py#_prompt_for
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 拆层隔离提示词只留槽位短标签，记忆包和研发记忆整段不得进入。
verify: pyw -3 -u -m unittest tests.test_warm_start_guardrails.TestMemoryPollutionTrace.test_layer_isolate_prompt_drops_memory_dump
applies: scripts/pmem_layer_split/isolate.py 组装隔离提示词时。
aliases:
- 拆层污染
- 隔离提示词
source:
  conversation: 8434809b-e30b-410f-9267-50d21ac61575
---
用户要求防住记忆污染。
拆图层隔离不走 Warm-Start。
keep/remove 里若出现 Warm-Start、style_redline、art_decision、.memory、候选红线、收敛踩坑、必须避开红线或优先复用定稿，整段改回槽位 id 或默认删除句。
正常短标签（如木船、码头）保留。
裁切像素仍是外观地面真相。
