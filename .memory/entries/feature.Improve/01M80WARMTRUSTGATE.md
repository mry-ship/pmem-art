---
id: 01M80WARMTRUSTGATE
module: feature.Improve
entity: WarmStartGuardrails
kind: correction
status: active
supersedes:
- 01M750C5HHHMNDH58AM7BD2BHT
anchors:
- improve/warm_start.py#gate_style_memory
- improve/warm_start.py#build_warm_start_pack
revision: local:trust-recheck
author: cursor-agent
note_date: '2026-11-23'
summary: 红线/拍板须 verified 才注入；recipe 仍不进 prompt
verify: unittest tests.test_warm_start_guardrails.TestMemoryPollutionTrace -q
applies: build_warm_start_pack 生成 prompt_block 时
aliases:
- 优先复用定稿方向
- 未确认记忆
---
仍成立：prompt_block 禁止列出 top_recipes /「优先复用定稿方向」；旧 recipe 只可参与置信与 UI。
更正：红线与审美拍板不再「只要活着就可注入」——须 trust=verified|canonical，且与四格 forbid 肯定句不冲突；candidate 与缺 trust 只进排除记录。
口味 keep/banned 与知识卡仍可注入，但会过 forbid 冲突过滤。
