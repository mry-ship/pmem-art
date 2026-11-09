---
id: 01M70R6JNHQXBMTPGBQFW6GA6S
module: feature.SkillsKit
entity: NoPostKeyFakeAlpha
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/alpha_policy.py#post_key_allowed
- skills_kit/export_mode_c_icon.py#as_delivery_rgba
revision: git:ee1870b
author: yanghu
note_date: '2026-11-10'
summary: 禁止后抠/挖洞冒充透明底交差
scope: project
verify: export_mode_c_icon 无 --key-flat-bg；结算 isolation_mode=opaque_isolation；正文禁后抠
applies: Cursor GenerateImage 或不支持 alpha 的生图路径；icon.c/UI/per_cell 要透明底时
---
试过：Cursor 生出实心底后，用角点抠色、export_mode_c_icon 挖洞、本地羽化冒充真 alpha。
结果：毛边/漏抠、四角假透明、与引擎能力不符，还把合同锁死在真 alpha。
排除：不支持透明的引擎禁止后处理抠图交差；口语要透明底时改隔离底直接生成。透明引擎应 API/提示词直接出 alpha，而不是先实心底再抠。
