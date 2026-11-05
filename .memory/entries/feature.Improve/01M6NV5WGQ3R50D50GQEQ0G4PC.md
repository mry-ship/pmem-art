---
id: 01M6NV5WGQ3R50D50GQEQ0G4PC
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py#build_warm_start_pack
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: Warm-Start 按任务域过滤口味与跑题 recipe，红线注入封顶
verify: pyw -3 -m pytest tests/test_warm_start_guardrails.py -q
applies: converge generate / warm-start 组装 prompt_block 时
---
出图负向修复（注入层，不改历史档案语义）：
  1) banned_habits 按主题域过滤，UI/建筑不再灌入糖果/气球档差等 merge 禁令，通用霓虹油腻等仍保留；
域内任务优先保留域禁令。
  2) prompt 增加正向保留 keep_phrases，并补充建设性 keep。
  3) recipe/红线若带圣诞/软糖/乐器等强主题而当前任务没有，则剔除，避免 App Icon 圣诞高分条污染其它 icon。
  4) 红线注入最多 3 条，置信度按注入数计算，减轻堆约束。
测试：tests/test_warm_start_guardrails.py
