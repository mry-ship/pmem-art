---
id: 01M6N6VG3F2DFJP7BBKDX69HK5
module: feature.SkillsKit.MergeLadder.Delivery
entity: MergeDelivery
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py#pmem-merge-ladder
- .agents/skills/pmem-merge-ladder/SKILL.md
- skills_kit/route_ask.py
- skills_kit/install.py
revision: git:e5571b3
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: 合成梯默认整表一组（8档），点名逐格才per_cell
verify: SKILL 与 AGENTS.md 写默认整表一组；unittest tests.test_skill_router 通过
applies: 玩家要合成梯/merge/一组升级链且未点名逐格
aliases:
- merge默认整表
verified: '2026-11-10'
verified_at: '2026-11-10T14:24:43.192+08:00'
---
需求来源：画师反馈一组merge就是整表一组，默认8个；
除非给参考或点名固定数量。必须保持：
  1)默认delivery=overview_sheet、levels=8、无参考常见2x4；
  2)有格子参考则levels/版式跟参考；
  3)点名数量跟点名；
  4)仅点名一档一张/逐格/单张/per_cell才走per_cell；
  5)禁止未点名逐格却单张狂刷。
入口：/pmem-merge-ladder；
源在skills_kit/skill_specs.py，install同步各端技能与AGENTS/CLAUDE/pmem-art.mdc；
路由人话route_ask.py。
