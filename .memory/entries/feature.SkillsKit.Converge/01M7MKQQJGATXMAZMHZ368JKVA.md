---
id: 01M7MKQQJGATXMAZMHZ368JKVA
module: feature.SkillsKit.Converge
entity: WarmStartKeepBleed
kind: conclusion
status: active
supersedes: []
anchors:
- improve/warm_start.py#filter_keeps_for_task
- improve/warm_start.py#_TOPIC_PATTERNS
- skills_kit/converge.py
revision: git:e48df70
author: 1002378395@qq.com
note_date: '2026-11-17'
summary: 无强主题标记的 GH 货柜 keep 会漏过滤灌进非 merge Prompt
verify: pyw -3 -u -c "from improve.warm_start import filter_keeps_for_task; print(filter_keeps_for_task(['休闲merge海鲜货柜真机表面'],
  'character.DogCollage', '狗狗拼板'))" 期望过滤后为空
applies: 非 merge 模块/目标跑 converge start/generate 且 taste.keep_phrases 含 GH 货柜句时
aliases:
- Warm-Start串味
- 货柜keep漏过滤
- 海鲜货柜灌进普通图
source:
  conversation: 7756ad1a-6c4d-4c92-a613-772055b4f6be
---
现象：dog_collage（character.DogCollage / draw.ordinary）最终 Prompt 被灌入「软立体糖釉玩具货柜」「休闲merge海鲜货柜…龙虾/蟹/蚝」。
路径：taste.json keep_phrases → improve/warm_start.py build_warm_start_pack → filter_keeps_for_task → prompt_block → converge generate merge_warm_start_prompt 并入每轮最终 Prompt。
根因：filter_keeps 仅当 keep 命中 _TOPIC_PATTERNS 强主题且与任务 ctx 无交集时才丢弃；
货柜/糖釉/Gossip Harbor/海鲜等短语未进 merge_ladder 等主题正则，scopes_in 为空 → 当作通用正向保留放行。
非 merge 模块 ctx 也为空时更拦不住。
影响：非 merge 普通图被 GH 货柜表面带偏，看起来像「提示词变写实/变软立体」。
证据：对 character.DogCollage 跑 filter_keeps_for_task，上述两条 keep 原样返回。
修复方向（未做）：给 GH/货柜/糖釉/海鲜 打 merge 主题标，或非 merge 任务硬丢含货柜糖釉的 keep。
