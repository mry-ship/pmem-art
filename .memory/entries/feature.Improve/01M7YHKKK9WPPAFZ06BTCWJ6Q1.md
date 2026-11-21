---
id: 01M7YHKKK9WPPAFZ06BTCWJ6Q1
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py#build_warm_start_pack
- improve/warm_start.py#conflicting_forbid_phrase
revision: git:0b7e1e8
author: yanghu
note_date: '2026-11-21'
summary: 暖启排除记录写出未注入原因
verify: python3 -m unittest tests.test_warm_start_guardrails.TestMemoryPollutionTrace
  -q
applies: build_warm_start_pack 组装 inject_trace 时
---
需求来源：注入过滤已经丢掉缺 trust、候选、作废、跨模块和与四格冲突的记忆，但排除原因只覆盖过闸后的红线/拍板，调用方看不出哪条没进提示词。明确禁止原先整句碰到「避免/禁止」就放行，短于 4 字的禁止词也不拦。
必须保持：recipe 摘要仍不进 prompt_block，不写「优先复用定稿方向」；不改记忆文件 status；已确认且与四格不冲突的红线/拍板仍注入。写着避免/禁止该词的分句不算冲突。
落地：未进入候选池的 recipe/红线/拍板写入 inject_trace.excluded。
留在池内的 recipe 另记「不进提示词」。
conflicting_forbid_phrase 按分句判断：肯定句里的禁止词才冲突，避免句不算。
同一规则用于红线、拍板、keep 和知识卡。
入口：improve/warm_start.py build_warm_start_pack。
