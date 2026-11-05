---
id: 01M6P1XAG967EG48WEFNQHSSN2
module: feature.SkillsKit
entity: StyleLockDeliveryContract
kind: risk
status: active
supersedes: []
anchors:
- .agents/skills/pmem-style-lock/SKILL.md
- skills_kit/skill_specs.py
- feedback.py
revision: git:838086c
author: 1002378395@qq.com
note_date: '2026-11-05'
summary: style-lock 的配方承诺、模块默认与实际写入路径不一致
verify: 对照 .agents/skills/pmem-style-lock/SKILL.md 的 description/步骤与 feedback.py 的
  role、module 缺省分支、写入 kind；再核实修订后的技能合同与归档结果。
applies: 执行 /pmem-style-lock，尤其玩家未指定目标模块时。
source:
  conversation: 01a1abb8-0adc-7403-bf8c-04a43e507842
---
审计发现 /pmem-style-lock 的 description 承诺将风格基准写成 art_decision + recipe，但正文只调用 feedback --kind art_decision 和 --kind style_redline；
feedback.py 将 art_decision 作为 reference 类型写入，并未显式创建 recipe。
另当 feedback 未给 --module 时会写入 _inbox/pending，而非立即归入项目/模块正式记忆。
若不明确默认作用域并补齐 recipe 写入或修正文案，用户以为风格已锁定，后续实际召回可能不符合预期。
