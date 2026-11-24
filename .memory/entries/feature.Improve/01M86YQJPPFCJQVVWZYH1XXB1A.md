---
id: 01M86YQJPPFCJQVVWZYH1XXB1A
module: feature.Improve
entity: PromptPollution
kind: feature
status: active
supersedes: []
anchors:
- improve/warm_start.py#gate_style_memory
- improve/warm_start.py#_prior_sku_bleed
- improve/warm_start.py#_foreign_artifact_bleed
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 已确认的红线、拍板、口味和知识卡不得把别的物件或其他交付物写进提示词。
verify: pyw -3 -u -m unittest tests.test_warm_start_guardrails.TestMemoryPollutionTrace
applies: 生图提示词经 improve/warm_start.py 组装时。目标自己点名了该物件或该交付物时不拦。
aliases:
- 记忆污染
- 串题材
- 他趟物件
source:
  conversation: 8434809b-e30b-410f-9267-50d21ac61575
---
用户要求再次检查并防住记忆污染。
生图 Warm-Start 只读 .memory-art，不读研发记忆 .memory。
未写信任、candidate、废止条目仍不进提示词；
recipe 只参与置信、不进提示词。
即使是 verified/canonical，红线注入句、审美拍板、禁用习惯、口味偏好和知识卡正文，只要点了当前目标没有的他趟具体物件（如露莓果酱、热可可、HarborHotCocoa、草莓软糖SSS），或剥掉本趟同族词后仍是别的交付物（如主菜单任务里的 currentColor、合成梯），就不进提示词。
任务句里出现「主菜单」不再放行其他交付物。
泛化现象红线（如避免按钮没有按下态）仍注入。
