---
id: 01ART007SCENEDECISION
module: scene.FloatingRuins
entity: LightingDirection
kind: art_decision
status: active
note_date: '2026-10-21'
verified: '2026-10-24'
author: 场景主美·陆遥
summary: 浮空遗迹全局光照锁定『左上 45° 暖金主光 + 右下 45° 远山黛蓝冷阴影』，相机固定 30° 等轴测正交透视
verify: 所有独立建筑物件（石柱、星盘祭坛、浮石）投影方向必须指向右下方（+45°），禁止出现顶光或右侧逆光物件
applies: 第一幕 FloatingRuins 所有背景概念图、地块 Tilemap 与独立可摆放建筑物件（Props）
palette: ["#0F172A", "#1E3A4B", "#F4F1EA", "#F59E0B", "#2DD4BF"]
assets:
  - path: assets/scene/floating_ruins_keyart_v2.png
    role: anchor
    caption: "✅ 场景主视觉与光影方向基准图：左上45°天光束 + 等轴测白玉浮台 + 右下投影"
    sha256_16: 4776c829d14a6b63
anchors:
  - assets/scene/floating_ruins_keyart_v2.png
---
**【场景光影与透视铁律】**
AI 生成单个场景物件（Prop）并拼合到 Unity 2D 等轴测场景时，最常见的穿帮是**各个物件的受光面不一致**。
- **主光源（Key Light）**：固定来自画面**左上方 45°**，色温偏暖鎏金（`#F59E0B` ~ `#F4F1EA`）。
- **背光面与投影（Shadow）**：统一朝向画面**右下方 45°**，阴影色相必须融入远山黛蓝（`#1E3A4B`）与玄青（`#0F172A`），严禁使用纯黑死黑（`#000000`）画阴影。
- **法阵自发光**：地面凹槽内的星轨刻痕使用 `#2DD4BF`（秘色青瓷）叠加层。
