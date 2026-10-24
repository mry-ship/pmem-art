---
id: 01ART006EXPRCORRECTION
module: character.Astra.Expressions
entity: ExpressionSheet
kind: visual_correction
status: active
supersedes: [01ART000OLDEXPR]
note_date: '2026-10-23'
verified: '2026-10-23'
author: 角色组长·苏澈
summary: 表情差分瞳光色阶修正：常态青瓷(#2DD4BF) / 战斗鎏金(#F59E0B) / 受击朱砂(#E11D48)，待修惊愕草稿尺寸与漏去背问题
verify: 检查 astra_expressions_2x2.png 四个象限瞳色与义眼发光色完全对应；修复 astra_expr_shock_draft.png 的 768x768 RGB 违规
applies: AVG 剧情对话立绘差分组件
palette: ["#2DD4BF", "#F59E0B", "#34D399", "#E11D48"]
assets:
  - path: assets/character/astra_expressions_2x2.png
    role: approved
    caption: "✅ 已验收 2x2 表情差分合集（1024x1024 RGBA）：平静/战斗/微哂/受击"
    sha256_16: 243e875ea4de4aff
  - path: assets/character/astra_expr_shock_draft.png
    role: rejected
    caption: "⚠️ 待修复草稿：新增『惊愕』差分时 AI 导出了 768x768 且为 RGB 无透明通道（被 pmem-art 质检拦截）"
    sha256_16: 000000000000dead
anchors:
  - assets/character/astra_expressions_2x2.png
  - assets/character/astra_expr_shock_draft.png#alpha
---
**【视觉勘误与质检拦截记录】**
1. **情绪与星盘义眼联动色**：阿斯特拉面部克制，情绪主要通过**左眼黄铜星盘义眼的发光色**强化传达：
   - `Calm（平静）`：秘色青瓷光（`#2DD4BF`）
   - `Battle（星盘觉醒）`：炽热鎏金光（`#F59E0B`）
   - `Smile（微哂）`：翠玉柔光（`#34D399`）
   - `Damaged（受击警报）`：朱砂绛红光（`#E11D48`）
2. **⚠️ 当前待处理问题**：`assets/character/astra_expr_shock_draft.png` 刚由 AI 重新生成覆盖，哈希已变更（触发 `stale: true` 需复核），且实测分辨率为 `768x768`、色彩模式为 `RGB`（丢失 Alpha 透明通道），请 AI 美术 Agent 按 `1024x1024 RGBA` 重新执行去背与扩图。
