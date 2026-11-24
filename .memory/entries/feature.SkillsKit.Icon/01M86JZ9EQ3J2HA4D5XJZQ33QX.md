---
id: 01M86JZ9EQ3J2HA4D5XJZQ33QX
module: feature.SkillsKit.Icon
entity: IconCropMeansBBox
kind: conclusion
status: active
supersedes: []
anchors:
- skills_kit/skill_specs.py
- skills_kit/converge.py#_icon_crop_note
- skills_kit/prompt_scale.py#compose_continuation_prompt
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 合同把裁到四边写成外接框 72–80%，量到就不再要求裁满
verify: 对照 skill_specs Mode A 「外轮廓被画面裁到 72%–80%」与 converge._icon_crop_note：短边≥0.72
  返回空字符串。tilematch-icon-top 短边 77/82/83%
applies: icon.a 母版把英雄外接框当成安全区，并同时要求外轮廓被四边裁到
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
Mode A 把两种几何写成同一句：「英雄外轮廓被画面裁到 72%–80%」。外接框 76% 是主体悬在中间、四周留一圈底；外轮廓被四边裁开、底色只留四角，外接框会接近满幅。两者不能同时成立。
icon_subject_span 量的是外接框。_icon_crop_note 在短边≥72% 时返回空，不再写裁切句。所以悬空的 77%–83% 被当成裁切已经合格。
tilematch-icon-top 三轮短边 77%、82%、83%，安全区 8.4、8.6、8.6，门槛没有替换正式分，加权后仍是 8.57、8.63、8.73。
第 2 轮起垫这张悬空成图，续写句是「只改这一处」加「没点名的地方保持垫图」，留白被垫图锁住。
厚糖釉只出现在草莓上，因为禁用「油腻高光」没有随厚体积句一起拿掉。
