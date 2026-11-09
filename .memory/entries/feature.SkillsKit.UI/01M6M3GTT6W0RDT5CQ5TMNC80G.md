---
id: 01M6M3GTT6W0RDT5CQ5TMNC80G
module: feature.SkillsKit.UI
entity: UITopBarIA
kind: correction
status: active
supersedes: []
anchors:
- skills_kit/converge.py
- skills_kit/converge_policy.py
- skills_kit/converge_loop.py
- skills_kit/install.py
- skills_kit/skill_registry.py
revision: git:d22af79
author: yanghu
note_date: '2026-11-05'
summary: RM真主页：顶栏单行+底栏五Tab；禁右侧四钮瞎编
verify: refs/rm_home_ui_real.png 存在；skill_specs 落位要求先看真实按钮截图
applies: /pmem-ui 主菜单对标与 /pmem-icon Mode A 商店对标
source:
  conversation: ccfc4c53-773f-4c77-90b0-4088c1330449
---
用户2026-11-05怒指：此前没有下载 Royal Match 真实 UI 按钮界面，拿宣传/叙事图硬猜落位。
已从 Flomob 落盘 rm_home_ui_real / leaderboard / settings / appicon。
真主页骨架：顶栏 头像|币|心|星|右上齿轮 同排；中下 Level+Area；底栏五 Tab（Home 城堡居中）；商店入口常为点金币。
排除：右侧 Shop/Events/Mail/Rewards 四 squircles 当主骨架；
把「禁 Clash 对战底栏」误读成「休闲也禁底栏」；
用 royal_match_main / rm_prop_ui_crop 叙事图当 HUD 合同。
App Icon 真图：国王半身撑满，非小静物。
