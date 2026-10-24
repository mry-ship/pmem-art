---
name: art-icon
description: 【截图可见·必读】/pmem-icon 与 /art-icon 生成图标集时，关键单枚与不合格批次强制「最多8轮、合格线≥9.5」闭环自评收敛（生1张→打分挑刺→<9.5叠加修正→满8轮挑最高分→评分总表）。流水线对标 jezweb：先锁 style-spec → 约5个一批 SVG（统一 viewBox/currentColor/stroke）→ preview.html。触发例：「/pmem-icon 给青瓷RPG做一套24px导航图标」「/art-icon home settings inventory」。
---

# `/pmem-icon`（别名 `/art-icon`）— jezweb 式一致化图标集 / SVG 取向生成

## 怎么用（复制即用）
```text
/pmem-icon 给本项目做一套 24px Clean 预设导航+背包图标（SVG），输出 style-spec 与 preview.html
/art-icon home settings inventory craft map quest
/pmem-icon [拖入品牌样张] 按这个线宽与圆角补齐：phone email location
```

## 原理（截图摘要）
1. 先锁 **style-spec**（Clean/Sharp/Soft/Minimal/Bold）→ 2. SVG 硬规则（同 viewBox · `currentColor` · 同 stroke）→ 3. 约 5 个一批生成 + 一致性审查 → 4. 交付 `icons/` + `preview.html` → 5. 关键枚 **强制 8轮 ≥9.5** 收敛并写入记忆

你现在运行在 **pmem-art 图标集模式**（对标 jezweb `icon-set-generator`）：先锁 **一份 style-spec**，再批量生成，保证 stroke、圆角、视口、视觉重量一致——**禁止**从 Lucide/Heroicons 随便拼一套「看起来差不多」的通用库图标冒充项目定制集。

---

## 一、适用场景
- 网站 / App / 游戏 HUD 的 **成套自定义图标**
- 需要 SVG（优先）或统一栅格（如 64×64 透明底道具图标）且 **整套同系**

## 二、标准流程（Brief → Spec → Batch → Review → Converge）

### Step 1：理解项目与图标清单
收集：行业/项目气质、品牌色（即使 SVG 用 `currentColor` 也影响线型选择）、大约数量。
按组建议清单（可让用户增删）：
- Navigation / Communication / Trust / Actions / Industry-Specific（或游戏：Inventory / Combat / Status / Crafting）

### Step 2：锁定 Style Spec（生成前必须确认）
推荐预设起步：

| Preset | 适用 | Stroke | Caps/Joins | Corners |
|--------|------|--------|------------|---------|
| Clean | 多数业务站 | 1.5px | round/round | 2px |
| Sharp | 科技/硬核 | 1.5px | square/miter | 0px |
| Soft | 亲和/休闲 | 2px | round/round | 4px |
| Minimal | 编辑/优雅 | 1px | round/round | 0px |
| Bold | 高识别/无障碍 | 2.5px | round/round | 2px |

写入 `icons/style-spec.json`（含 grid/viewBox、strokeWidth、linecap、linejoin、padding、opticalBalance、icons[]）。

### Step 3：SVG 硬规则（整套必须统一）
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="{grid}" height="{grid}"
  viewBox="0 0 {grid} {grid}" fill="none" stroke="currentColor"
  stroke-width="{strokeWidth}" stroke-linecap="{…}" stroke-linejoin="{…}">
  <!-- paths -->
</svg>
```
1. **只用 `currentColor`**，禁止写死 `#000` / `blue`
2. **同一 viewBox**、同一根节点 stroke 属性
3. 无根节点 transform；无无用 id/class
4. 坐标最多 2 位小数；保持 padding；视觉居中（光学校正）
5. 路径尽量少；简单图标略加重以平衡视觉重量

若用户要的是 **游戏道具栅格图标**（非 SVG）：仍先锁「线宽/圆角/色板/投影」style-spec，再批量生成透明底 PNG，规则改为「同色板同描边同投影」，并可用 `converge` 打磨单枚。

### Step 4：分批生成（约每批 5 个）+ 一致性审查
每批完成后检查：stroke 是否漂移、圆角是否混用、有无图标明显偏轻/偏重、是否贴边。
全部完成后生成：
```
icons/
├── style-spec.json
├── preview.html      # 含 1x/2x 与深色底对比，内联 SVG
├── home.svg
└── …
```

### Step 5：关键图标 8轮9.5 收敛（可选）
用户点名某枚「不对」或一致性审查不通过时：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module ui.Icons
# 生成 → 自评（侧重：规格一致性 2.5 + 识别度 2.5 + …）→ round → finish --apply
```

### Step 6：沉淀
```bash
python3 pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module ui.Icons --kind art_decision
python3 pmem_art.py ingest icons/preview.html -p "icon set preview" --apply   # 若适用
```

## 三、交付检查清单
- [ ] 全部 SVG 同 viewBox / stroke-width / linecap / linejoin
- [ ] 全部 `currentColor`
- [ ] 视觉重量平衡、padding 一致、光学居中
- [ ] 文件名 kebab-case；`preview.html` + `style-spec.json` 齐全
- [ ] 若跑了收敛：附评分总表
