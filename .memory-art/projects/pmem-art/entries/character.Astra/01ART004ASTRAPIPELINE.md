---
id: 01ART004ASTRAPIPELINE
module: character.Astra
entity: SpineLayering
kind: pipeline_constraint
status: active
note_date: '2026-10-21'
verified: '2026-10-24'
author: 动效绑定·周野
summary: 立绘交付必须为 1024x1024 RGBA 预乘透明通道，四周留足 16px 安全边距，按 8 大标准图层命名拆分供 Spine 绑定
verify: 运行 pmem_art.py validate 检查分辨率=1024x1024、mode=RGBA、边缘 16px alpha=0，无半透明白边杂色
applies: 所有进入 Spine 2D 骨骼绑定管线的角色立绘与差分
palette: ["#0F172A", "#2DD4BF", "#F59E0B"]
specs:
  resolution: "1024x1024"
  alpha_required: true
  premultiplied_alpha: true
  safe_margin_px: 16
assets:
  - path: assets/character/astra_standing_v3.png
    role: anchor
    caption: "1024x1024 RGBA 标准透明通道立绘（四周留空 > 16px）"
    sha256_16: 9c771d1f63976fb6
  - path: assets/character/astra_turnaround_sheet.png
    role: approved
    caption: "2048x1024 正/侧/背三视图（对齐等高参考线，供 3D 建模与 Spine 拆分对位）"
    sha256_16: c5cdda6eafdd5fb0
anchors:
  - assets/character/astra_standing_v3.png#alpha
  - assets/character/astra_turnaround_sheet.png
---
**【管线硬性技术规范 · Spine 绑定与透明通道】**
1. **画布与安全边距**：单人立绘统一 `1024x1024`（三视图合集为 `2048x1024`），头顶星盘光环与裙摆底端距离画布边缘必须保留 **至少 16px 纯透明安全区**，防止 Spine 网格变形（Mesh Deform）呼吸起伏时发生切边。
2. **去背与预乘 Alpha（Premultiplied Alpha）**：AI 生图经过 `RMBG-2.0` 抠图后，必须执行 `4px Defringe（去白边）` 并导出为预乘 Alpha PNG，严禁残留灰白半透明像素圈。
3. **Spine 8层标准部位命名**：
   `halo_back`（背后星盘环）→ `hair_back`（后发）→ `cloak_main`（外袍）→ `torso_tunic`（内衬躯干）→ `jade_pendant`（腰间青瓷佩）→ `head_base`（脸部底图）→ `eye_monocle_L`（左眼星盘义眼独立层，用于旋转动效）→ `hair_front`（前刘海）。
