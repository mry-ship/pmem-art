---
id: 01ART003ASTRAREDLINE
module: character.Astra
entity: Proportions
kind: style_redline
status: active
note_date: '2026-10-20'
verified: '2026-10-24'
author: 角色组长·苏澈
summary: 阿斯特拉严禁画成5~6头身二次元幼态Q版！必须严格保持 7.5 头身修长比例与左眼(画面右侧)黄铜星盘单片义眼
verify: 测量全身立绘高度与头高比值在 7.3~7.6 之间，且左眼（观者右侧）必须佩戴十字星芒黄铜星盘义眼
applies: character.Astra 及其所有换装、表情与宣传图子模块
aliases: [阿斯特拉比例, 左眼义眼红线, 禁Q版]
palette: ["#0F172A", "#F4F1EA", "#2DD4BF", "#F59E0B", "#E2E8F0"]
assets:
  - path: assets/character/astra_standing_v3.png
    role: approved
    caption: "✅ 正例定稿：7.5头身修长比例、月白银发、左眼(画面右侧)星盘义眼、玄青鎏金长袍"
    sha256_16: 9c771d1f63976fb6
  - path: assets/character/astra_rejected_chibi_neon.png
    role: rejected
    caption: "❌ 废案打回：5头身大头Q版比例 + 洋红发色 + 漏画左眼星盘义眼（早期未加 ControlNet 骨点导致）"
    sha256_16: 7e3a8d54eef514cf
anchors:
  - assets/character/astra_standing_v3.png#proportions
---
**【角色核心防翻车红线】**
1. **头身比铁律**：阿斯特拉是统御星轨的“司辰”，气质清冷威严，**必须严格锁定 7.5 头身**（生图时必须挂载 `openpose_full` 7.5头身骨架图，严禁直接裸跑 txt2img 导致退化成 5~6 头身萌系大头娃娃）。
2. **不对称视觉锚点（左眼星盘义眼）**：角色自己的**左眼（即正视图画面右侧）**佩戴黄铜星盘单片义眼（带十字亮白星芒），右眼（画面左侧）为正常深青色瞳孔。**镜像翻转草图时极易把义眼翻到右眼，提交前必查！**
3. **发色与服饰**：发色为月白银灰（`#E2E8F0`），绝不可偏紫或偏粉。腰间必挂一枚秘色青瓷玉佩（`#2DD4BF`）。
