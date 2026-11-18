---
id: 01M7PVW5RZA56XY4QDPZEKS0PE
module: feature.SkillsKit.Converge
entity: JudgePadCopy
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_describe_next_pad
revision: git:fdcc718
author: 1002378395@qq.com
note_date: '2026-11-18'
summary: 审图续轮不要把最高分成图说成唯一垫图
verify: 审图未达标文案在 pad=auto 时含「垫图仍用最初那张」，不含「下一轮先垫这张再出图」
applies: 审图未达标要告诉执行侧下一轮垫哪张时
aliases:
- 审图先垫这张
- 垫图跟着成图漂
source:
  conversation: 0abec877-f686-4dac-88fe-ad9c7f38c9cb
---
现象：登记策略写着每轮垫最初参考，审图没达标却另印「下一轮先垫这张」并指向最高分成图，再写「生图参考图只用这一张」。执行侧照这句把成图交给生图模型，第 2、3 轮不再看见最初参考，画风沿已经更实的成图走。
原因：这句话用的是最高分成图，没有走垫图策略。converge next 当时已经区分了「垫最初参考 / 上轮成图不链」。
影响：所有共用审图续轮文案的技能都会被这一句带偏，不用按技能各改一份策略。
排除：不要把这句再改回「先垫最高分成图」。链成图只留给 pad=previous 和已证明换机位。
