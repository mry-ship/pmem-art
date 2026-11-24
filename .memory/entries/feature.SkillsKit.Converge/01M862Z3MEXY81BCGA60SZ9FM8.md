---
id: 01M862Z3MEXY81BCGA60SZ9FM8
module: feature.SkillsKit.Converge
entity: EmptyStyleRefNoPad
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/converge.py#_resolve_pad_auto
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 口头参考竞品不会垫图，空参考加 pad=auto 每轮都不垫
verify: ref_image 为空且 pad_mode=auto 时 emit 打印不垫图；第 2 轮策略含 pad=auto→style_ref 且垫图路径为空
applies: 玩家口头点名竞品气质、对话里没有可垫的风格图文件、pad 仍是 auto
aliases:
- 不垫图
- 没垫图
- pad=auto
source:
  kind: conversation
---
口头说「参考某款竞品图标」不会变成垫图。
竞品商店图又禁止当垫图抄像素、抄构图，于是开跑时 style_ref 为空。
pad=auto 只垫开跑时那张风格参考，不拿上一轮成图接着垫；
参考是空字符串时，每一轮都打印不垫图（第 1 轮原因 no_prior_plate，第 2 轮原因仍是 pad=auto→style_ref，但路径为空）。
medium 再在提示词里锁「不改机位」。
第 1 轮若画成斜俯视摆件，后面几轮改不了机位，图标安全区门槛（识别度/安全区低于 8.0 就改取该维）会把正式分压在 7 分上下。
要垫，必须有一张允许垫的风格图文件进 ref_image；
只有文字气质句不够。
