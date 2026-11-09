---
id: 01M6M2KRHHCFS38HDS2XP431Z5
module: feature.SkillsKit.Router
entity: RouteKeywordFalseFire
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#plan_route
- skills_kit/route_bank.py#confidence_for
- skills_kit/route_gate.py#check_route_gate
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: 近邻不同意仍可 execute_ok；子串误判会直接开画或拉起全清单
verify: python3 -c "from skills_kit.route_bank import advise_route; a=advise_route('再跑一遍这张猫');
  assert a['execute_ok'] and len(a['route_ids'])>=8"
applies: 未点名具体技能、走 /pmem-agent 与 pmem_art.py route 时
aliases:
- 调用链
- 误路由
- execute_ok
- 再跑一遍
source:
  conversation: bebd9fbe-2671-4d95-aa71-a5515c6fdbf6
---
现象：advise_route 在规则误判时仍常 execute_ok=true。confidence_for 在近邻 route_ids 与本判不同、但分数≥0.25 时仍给 medium，不否决。
实测（2026-11-05）：别画成赛博/不画背景→审图；
归位到画面中心→归档（近邻是普通图仍放行）；
L1缓存→合成梯；
主视觉+微笑→变体（近邻是原画）；
以后都用暖色还要画→只锁风格；
知识卡收下→普通图开画；
再跑一遍这张猫/同范围→九支全清单且 execute_ok；
题材不变但换成一只猫且走普通图→保留题材短路吃掉换题材。
/pmem-draw 加合成梯在 plan_route 是普通图（点名 draw 屏蔽 merge）。
否定只看关键词左侧，序列帧不要仍停；
分镜感命中未识别工种。
registry phase（clone 先于 variant 先于 multi）与 plan_route 不一致。
route 闸门只认项目全局 last_advise（2 小时），goal 不像仍放行，不校验本次 start 的 route_id。
影响：总控若只信 execute_ok，会审图代替生图、归档代替立绘，或一句再跑一遍拉起九支。
