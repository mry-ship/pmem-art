---
id: 01M7QAXMZZKZK624S2RMW8QYCD
module: feature.SkillsKit.Draw
entity: LocalTouchupMode
kind: feature
status: active
supersedes:
- 01M7QA0RJES2SHS3SM6XRD9SSB
anchors:
- skills_kit/agent_router.py#_wants_touchup
- skills_kit/converge.py#_apply_touchup_caps
- skills_kit/skill_specs.py
- skills_kit/route_normalize.py
revision: git:f3998da
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 成图局部改走 draw.touchup 快通道：默认1枪、不凑三轮9.5
verify: unittest tests.test_skill_hardening.JobRemapTests tests.test_agent_route_stability
  -q；route 「修手指」banner 含局部改且 route_ids=[draw.touchup]
applies: 玩家对已有成图做局部瑕疵/小改，且不换题材机位身份时
aliases:
- 局部修改
- 局部调整
- 局部修
- 快改
- touchup
- spot fix
- draw.touchup
verified: '2026-11-21'
verified_at: '2026-11-21T15:48:12.571+08:00'
source:
  conversation: b3206fc3-5edb-4094-ad92-97f526162318
---
需求来源：整张大体合格时局部拧一处，不愿再走 route→技能→最多3轮 converge。
实现：新增 route_id=draw.touchup（挂 /pmem-draw「合同 · 局部改」）。
路由：JOB_REMAP（局部修/只改手/修一下这张等）+_wants_touchup 口语启发式+标准句「走局部改」；近邻与 colloquial 已补。
执行：converge start 遇 touchup → max_rounds≤2、默认 scale=low、自动盖轻量合理性、finish 允许人眼交（无六维也可）；禁止塞普通图三轮执行卡/交件拼板进 pack。
硬闸：锁机位身份题材未点名区；换题材/机位/整脸差分打回正式技能。
排除：不做真 mask inpaint（Cursor GenerateImage 无区域 mask）；放大清稿/换光/延展仍走普通图 remap。
