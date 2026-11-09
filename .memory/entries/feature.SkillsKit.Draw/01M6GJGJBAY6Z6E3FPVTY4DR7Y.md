---
id: 01M6GJGJBAY6Z6E3FPVTY4DR7Y
module: feature.SkillsKit.Draw
entity: StyleThenCloneKeyartGate
kind: exclusion
status: active
supersedes: []
anchors:
- skills_kit/agent_router.py#_style_verify_intent
revision: git:6a749ce
author: 1002378395@qq.com
note_date: '2026-11-03'
summary: 禁止锁风只入库交差；禁止原画软过构图回声
verify: 往后出图都用这张→仅 style.lock；锁风格再出验证图→style.lock+draw.clone
applies: 锁风格口语与原画垫风格样张
verified: '2026-11-05'
verified_at: '2026-11-05T23:10:01.441+08:00'
---
试过：锁风格只交卡片、靠画师自己再喊克隆；原画有样张时用「大体像风格」软过构图回声。
结果：电池测看不到验证图；原画贴样张机位/分区仍被说成大体对。
排除：不要把「锁风格…出图/验证」折成单独 style.lock；不要用软措辞放行 layout 回声。
改走：style_then_clone 串行；keyart layout_not_style_echo 清单+合同硬闸。
