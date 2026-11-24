---
id: 01M86Q20W2GP65YE84ZTWH4NTJ
module: feature.SkillsKit
entity: PromptPositiveNotBan
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/prompt_scale.py#get_converge_scale_profile
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 无参考去掉写实棚拍禁词，机位锁留下
verify: unittest tests.test_delivery_gates.DeliveryGateTests.test_no_ref_strips_keep_original_style_identity
applies: 没有风格参考图的首轮和续轮；续轮仍可能垫上一张成图
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
需求来源：玩家要拿掉写进提示词的排斥句。复核时发现把「没有 ref_image」当成「没有可锁的机位」会放开续轮。
必须保持：没有风格参考图时，约束尾写「跟提示词品类默认画风」，不写「禁止回落写实棚拍」。
同时仍留「不改机位」「不做整体 recompose」「不增删主体元素清单」和「保画风与机位」。
续轮垫的是上一张成图，ref_image 仍可以是空，机位不能跟着空参考一起放开。
没有风格参考图时仍拿掉「保持原图画风」和「性别、物种、年龄段」。有风格参考图时这两条留下。
正文写了四边裁或只留在四角时，仍由 drop_opposed 拿掉机位锁。
软糖修订句写半透明、宽柔高光、边缘暖散射。目标写成硬塑胶仍过不了闸。
适用：所有走 converge 的生图技能。
入口：prompt_scale.get_converge_scale_profile 的无垫图分支。
