---
id: 01M6N6TXJ880TDQVCGFA4SEZNM
module: feature.SkillsKit.MergeLadder.Delivery
entity: MergeDelivery
kind: correction
status: active
supersedes:
- 01M6GCHYGNAZF325EC5YDT8AB1
- 01M6GCJZYKNH0PPAT1EA05ZXRZ
- 01M6EBG7J4VPZJK15BM1RN1GSJ
anchors:
- skills_kit/skill_specs.py#pmem-merge-ladder
- skills_kit/route_ask.py
- skills_kit/install.py
revision: git:e5571b3
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 合成梯默认改为整表一组八档，不再默认per_cell
verify: python -m unittest tests.test_skill_router；route artist_say 含「默认整表一组出齐」
applies: pmem-merge-ladder 交付默认；玩家未点名逐格时
aliases:
- 合成梯默认整表
- merge默认一组
---
旧结论「无整表信号时默认 per_cell」作废。
新默认：delivery=overview_sheet、levels=8（常见2x4）；
有格子参考则 levels/版式跟参考；
玩家点名固定数量则跟点名；
仅当玩家明确说一档一张/逐格/单张/per_cell 才走 per_cell。
merge/一组/合成梯口语本身即整表交付，不必再说「放到一张图」。
