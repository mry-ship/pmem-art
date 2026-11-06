---
id: 01M6RDK6FHP9W0P2JDC0J22WKS
module: feature.SkillsKit
entity: DevOpsTalkGate
kind: correction
status: active
supersedes:
- 01M6RD0FRM0MM0MG2ZCXNHSFAV
- 01M6R7Q2FCV3C4K44SZNKGX9ZH
- 01M6R7Q084FCNMS5RA4TEWYA9N
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
- skills_kit/agent_router.py#plan_route
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: 查代码口语停在未识别；画面主体和锁风格仍按原契约
verify: py -3 -u -m unittest tests.test_route_false_fire tests.test_showcase_route
  tests.test_route_advise.RouteAdviseTests.test_style_then_clone_verify_image -q
applies: 总控 plan_route 遇到查代码、查仓库、查 bug 的口语时
aliases:
- 查bug
- 漏洞
- bugs复数
- review the code
source:
  conversation: 2fb9d6ff-529d-4817-aa0f-d09fd39d062b
---
主目录已用 _dev_ops_ask 替掉过窄的 _non_art_ops。
代码锚点（漏洞/bug/hooks/pytest/cli/skill/registry/agent_router/converge/代码/技能/路由/注册表等）命中且不是画面主体时，plan_route 停在 unrecognized，不进普通图。
bug/hook/skill 认单复数。
「深度检查整个项目」「再查一遍仓库」「review the code」也停。
画面主体仍放行：draw a cute bug、a pile of fish hooks、画一只 bug 怪物、用这个技能画一张猫、review the lighting、写个角色脚本。
裸图标停问仍在：对比页把图标和合成梯都再跑一遍 → icon_unspecified。
都按这张画一张窗边女孩（带图）走普通图；都按这张色板、以后按这张画仍是锁风格。锁完出验证图仍串 style.lock→draw.clone。
