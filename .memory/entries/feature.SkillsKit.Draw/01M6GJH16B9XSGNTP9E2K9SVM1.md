---
id: 01M6GJH16B9XSGNTP9E2K9SVM1
module: feature.SkillsKit.Draw
entity: StyleThenCloneKeyartGate
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_style_then_clone
- skills_kit/reasonableness_gate.py
- skills_kit/skill_specs.py
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 锁风验证串克隆；原画禁构图回声硬闸
verify: python -m unittest tests.test_route_advise.RouteAdviseTests.test_style_then_clone_verify_image
  tests.test_reasonableness_gate.TestReview.test_keyart_requires_layout_not_style_echo
  -q
applies: /pmem-style-lock 要验证成图；/pmem-draw 原画有风格样张
aliases:
- 锁风验证
- style_then_clone
- layout_not_style_echo
verified: '2026-11-05'
verified_at: '2026-11-05T23:10:01.441+08:00'
---
需求来源：电池测「锁风格为了出图」卡在只入库；原画贴样张构图被说成大体对，玩家要很好。
必须保持：
1) 口语含验证图/锁完出图/为了出图（且非以后/往后出图都按）时 plan_route 串 style.lock→draw.clone；
   点名 /pmem-style-lock 用 _style_verify_intent 同样升级；
   announce 为「按 锁风格→克隆验证 走了」。
2) 纯「往后出图都用这张色板」仍只走 style.lock。
3) 原画合同硬闸 layout_not_style_echo；合理性闸 keyart checklist 必含该项；有样张字样却无「只借画风/新机位」声明则启发式拦。
4) 标准句模板 style.then_clone 与二次 plan 对齐，避免 plan_conflict。
入口：skills_kit/agent_router.py、route_normalize.py、skill_specs 原画/style-lock、reasonableness_gate.py；
测试 test_route_advise / test_reasonableness_gate。
