---
id: 01M70WCJ0XEECS0ZWNBNFCYAJ1
module: feature.SkillsKit.Router
entity: RouteGrowObjectMerge
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_wants_merge
- skills_kit/route_ask.py#detect_vague_ask
- skills_kit/route_normalize.py#infer_signals
- tests/test_route_false_fire.py
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 越升越大+货柜物件可认merge；八档禁物件误开；否定合成梯不逼问
verify: python3 -m unittest tests.test_artist_talk_accuracy tests.test_route_false_fire
  -q
applies: 改 _wants_merge / route_ask / infer_signals / artist_talk 门禁时
aliases:
- 越升越大那条剑
- 八档剑
- 没有合成梯
---
问题：artist_talk#49「越升越大那条剑」被指代闸停；「八档剑」曾靠物件误开；否定句「没有合成梯」仍 clear_merge/infer 误触。
更正：
  1) 越升/越来越大 + 剑糖药水宝石道具 → merge；
  2) 八档只认真合成语境；
升档可+物件；
  3) 整表禁物件误开；
  4) clear_merge/soft_merge/infer 遇没有/不要/不做/别做合成梯一律关掉；
  5) 继续升档那条仍 soft 先问（设计如此）。
保持：太阳/星/宝箱/裸越升/道具整表导出 非 merge。
