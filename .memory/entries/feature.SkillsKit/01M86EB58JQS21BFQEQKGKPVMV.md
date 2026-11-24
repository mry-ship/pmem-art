---
id: 01M86EB58JQS21BFQEQKGKPVMV
module: feature.SkillsKit
entity: BriefRejectsRefPerson
kind: feature
status: active
supersedes: []
anchors:
- skills_kit/prompt_scale.py#drop_opposed_injections
- skills_kit/reasonableness_gate.py#_icon_a_store_default_issues
revision: git:bf5574f
author: 1002378395@qq.com
note_date: '2026-11-24'
summary: 正文拒绝参考人物时不再锁原图身份
verify: python -m unittest tests.test_prompt_conflict tests.test_reasonableness_gate
  -q
applies: 正文写了不要国王、不要人脸、不要胡子或不要皇冠，同时垫了别的角色图时
source:
  conversation: 1f7af752-c811-4865-9341-233eb6ffe881
---
核对前面几轮改动时补上两处漏。
正文已经写了不要画国王、不要人脸，档位约束仍把「保持原图性别、物种、年龄段与核心外观」贴进同一条。画风句留着，这句身份锁拿掉。
无参考图标默认句里的不要光点，合理性闸之前没查。现在缺了也不过。
登记复用定稿、审图同一次写下一轮定稿、高饱和压过避免过饱和，这三处对过代码和测试，没有再改。
