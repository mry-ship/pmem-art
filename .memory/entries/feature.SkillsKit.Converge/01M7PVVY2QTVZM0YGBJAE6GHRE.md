---
id: 01M7PVVY2QTVZM0YGBJAE6GHRE
module: feature.SkillsKit.Converge
entity: JudgePadCopy
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_describe_next_pad
- skills_kit/converge.py#_resolve_pad_auto
revision: git:fdcc718
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 审图续轮、next、emit 的垫图文案跟垫图策略，默认仍垫最初参考
verify: python -m unittest tests.test_converge_guards.TestPadAuto -v；审图续轮文案不再出现「下一轮先垫这张再出图」
applies: 有最初参考且 pad 不是 previous、也还没有换机位证据的闭环续轮
aliases:
- 垫图换成上一轮成图
- 生图参考图只用这一张
source:
  conversation: 0abec877-f686-4dac-88fe-ad9c7f38c9cb
---
需求：圣诞克隆那趟审图没达标时印了「下一轮先垫这张」并指向上一轮成图，执行侧把 GenerateImage 参考换成了成图，画风沿成图漂。登记策略仍是 pad=auto，每轮应垫最初参考。
必须保持：审图未达标、converge next、emit-prompt 三处用同一套说法。
auto/ref 写「垫图仍用最初那张」「上轮成图不要拿去垫」，改点只写进提示词。
只有 pad=previous，或 high/recompose 且轮次文字已证明换过机位，才写「垫第 N 轮成图」「生图参考图只用这一张成图」。
生图登记若传了别的图且策略不是链成图，要写明与策略不一致、应垫最初参考。
适用：所有走 converge 的出图技能（普通图、克隆、原画、变体、界面、图标、合成梯）共用这套文案，不按技能各写一份。
入口：converge judge 未达标续轮、converge next、converge generate --emit-prompt。
