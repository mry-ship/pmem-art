---
id: 01M7MP0Y8JGM3REFZBPXBK20B3
module: feature.Improve
entity: WarmStartGuardrails
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py#filter_keeps_with_audit
- improve/warm_start.py#tag_keep_phrase
- improve/taste_profile.py#apply_feedback_to_taste
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 静默三层：keep打标+非merge硬过滤+注入摘要不拦
verify: pyw -3 -m unittest tests.test_warm_start_guardrails -q 连续两次 OK；dog collage
  pack 无海鲜货柜句
applies: 非 merge 普通图/拼板与 merge 货柜共用同一 taste.keep_phrases 时
aliases:
- 静默三层
- keep打标
- 注入摘要不拦
source:
  conversation: 7756ad1a-6c4d-4c92-a613-772055b4f6be
---
需求：用户要简单、全程确认≤2次（确认名额只留给交付歧义）；美术记忆串味须静默修好，不中途阻塞。
必须保持：
1) 写入：apply_feedback_to_taste(kind=recipe) 用 tag_keep_phrase 存 {text,scopes}；hygiene dedupe 会给旧字符串 keep 补标。
2) 注入：merge_ladder 主题正则含货柜/糖釉/Gossip Harbor/海鲜/釉面高光等；
   filter_keeps_with_audit 对非 merge 丢 merge 主题 keep；
   长无标/「确认作为…锚点」fail-closed 不注入；
   短 universal 可留。
3) 可见不拦：pack.inject_summary + dropped_keeps；print_warm_start 与过程板展示，不进生图词、不问确认。
4) 默认不关 Warm-Start；merge 任务仍可注入 GH 货柜 keep。
入口：improve/warm_start.py；improve/taste_profile.py；improve/memory_hygiene.py；skills_kit/converge.py。
