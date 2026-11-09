---
id: 01M6RBM6MV3QZSW1A0XKJE34F3
module: feature.SkillsKit.Router
entity: DevOpsGateWordlistTightened
kind: correction
status: active
supersedes:
- 01M6RABZHFXV320X355C412DZD
anchors:
- skills_kit/agent_router.py#_dev_ops_ask
- tests/test_route_false_fire.py
revision: git:0e08123
author: 1002378395@qq.com
note_date: '2026-11-06'
summary: _dev_ops_ask 收紧:删 review/changes/接口/重构/哪里不对,补画面锚点与整句
verify: plan_route('review the lighting')/('the light changes at dusk')/('color changes
  across the sky')/('脸哪里不对')/('颜色哪里不对')/('接口处的金属接缝特写')/('重构角色比例') 都不是 unrecognized；plan_route('检查一下实现是否有问题').reason=='unrecognized'；unittest
  tests.test_route_false_fire 通过
applies: 改 agent_router 的 _DEV_OPS_ASCII/_DEV_OPS_CJK/_ART_OBJ 词表时
aliases:
- 研发口语闸词表过宽
- review changes 误停
- 接口重构撞画面
- 实现是否漏网
---
_dev_ops_ask 词表第二轮收紧（上一版 RouteGateAndRegistryFixes 为补 review recent changes/哪里不对 塞得过宽，撞美术口语）：
从 _DEV_OPS_ASCII 删 review、changes；
从 _DEV_OPS_CJK 删 接口、重构、哪里不对、技能、排查。
原因：review the lighting / review this key art / the light changes at dusk / color changes across the sky / 脸哪里不对 / 颜色哪里不对 / 接口处的金属接缝特写 / 重构角色比例 全被误当查代码停住。
_ART_OBJ_ASCII 加 key art、lighting；_ART_OBJ_CJK 加 颜色、金属、接缝、特写、脸、比例、角色（画面元素/反馈词，出现即判美术，压过弱代码信号）。
漏网修复：原 CJK 写的是 实现有没有/逻辑有没有，对不上「检查一下实现是否有问题」。改成整句四条：实现是否有问题/实现有没有问题/逻辑是否有问题/逻辑有没有问题；另补 单测/用例/这段代码。
取舍：review recent changes 现在走 draw.ordinary（不再 stop）——review/changes 在美术里太常见，宁可漏一句也不误杀。
保持：ASCII 仍走单词边界（cli 不吃 clip）；bug/hooks/pytest/skill/registry/agent_router/converge 等明确锚点不变。
