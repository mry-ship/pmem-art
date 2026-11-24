---
id: 01M86CM0MPVV45JE5BS8SJJQNW
module: feature.SkillsKit.Icon
entity: IconANoRefDefault
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/reasonableness_gate.py#_icon_a_store_default_issues
- skills_kit/prompt_scale.py#drop_opposed_injections
- skills_kit/skill_specs.py
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 图标用正面句写英雄，排斥句不过闸
verify: unittest tests.test_reasonableness_gate.TestReview.test_icon_a_identity_ban_fails
  tests.test_prompt_conflict.BriefBeatsInjectionTests.test_block_highlight_drops_soft_light
applies: icon.a 没有风格参考图、玩家也没写水彩/扁平/线稿/厚涂/矢量时
source:
  conversation: 7f125c36-73b8-4d6e-a766-5ab57808965e
---
需求来源：玩家说提示词里不要写「不要国王」这类排斥句，限制堆太多会把成图画差。
必须保持：英雄用正面句写它是什么。revised 里出现不要国王、不要王冠、不要胡子、不要披风、不要人脸，合理性不过。
不再强迫写不要投影、不要光点、不要周围留空、不要哑光黏土。裁切用正面句：外轮廓被四边裁开，底色只留在四角。72%–80% 只写给可读核心，不写给外轮廓。
中间图示按同品类已上架图标的完成度来画：一块材料铺满整个符号，高光成块。正文有高光成块时，口味包拿掉柔光。
先认品类再从商业对标表抽表面：休闲游戏图标用软立体、块面高光、圆润厚实；工具图标用克制微立体。非休闲不套货柜糖釉。
底与英雄冷暖相反，软卡通厚体积，一主光。玩家写了水彩、扁平、线稿、厚涂或矢量时跟玩家的画风，不强迫块面高光，仍要写中间图示这句。
正文写了糖釉时，禁用词拿掉油腻高光，留下廉价塑料感和过曝高光。
适用：所有 icon.a。
入口：/pmem-icon Mode A 的无参考默认句；reasonableness icon.a。
