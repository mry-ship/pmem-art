---
description: 【强制8轮≥9.6收敛】SpriteCook式 UI Kit/HUD/九宫格整套（pmem-art）
---

# `/pmem-ui`（别名 `/art-ui`）— SpriteCook 式 UI Kit / HUD / 九宫格整套生成

## 怎么用（复制即用）
```text
/pmem-ui 生成一套青瓷幻想风主菜单：九宫格面板 + 按钮 normal/pressed/disabled
/art-ui 做一套蒸汽朋克战斗 HUD（血条空满、技能槽），透明底
/pmem-ui [拖入概念图] 按概念拆出主面板九宫格、主按钮四态、进度条空/满、Tab 两态
```

## 原理（截图摘要）
1. `search` 召回 `ui.*` 红线与定稿 → 2. **概念先行** → 3. 透明组件表 → 4. 九宫格 + 状态族 → 5. **强制 8轮 ≥9.6**（每轮展示评分履历） → `finish` 打印履历 + **记忆静默写入**（勿旁白记忆）

你现在运行在 **pmem-art UI Kit 模式**（对标 SpriteCook UI Kit Builder：概念先行 → 组件表 → 九宫格切线 → 状态族）。**禁止**把整屏各控件零散各生一张再硬拼；必须先锁一个统一视觉语言的概念稿，再从同一概念抽出可复用零件。

---

## 一、适用场景
- 主菜单 / HUD / 暂停 / 设置 / 背包 / 对话框 / 商店 / 任务日志 / 角色面板 / 地图 / Game Over / Overlay
- 需要 **九宫格可拉伸面板、按钮多状态（normal/hover/pressed/disabled）、进度条空满态、标签选中/未选中** 的成套 UI

## 二、标准流水线（Concept → Sheets → 9-Slice → Converge）

### Step 0：确定屏幕类型与规格
确认：屏幕类型、平台（桌面/主机 vs 移动）、画幅（16:9 / 超宽 / 竖屏）、目标模块（如 `ui.MainMenu` / `ui.InventoryHUD`）。
```bash
python3 pmem_art.py search --module <ui.模块>
```

### Step 1：概念先行（Concept First）—— 不可跳过
1. 若用户丢入概念图：先做参考图视觉解构（构图分区、主辅色 HEX、金属/木纹/霓虹材质、控件密度），再进入组件抽取。
2. 若无概念图：先生成 **1 张完整屏幕概念稿**（整屏布局，统一材质与色板），用 `/pmem-draw` 同款 **8轮 >=9.6 收敛** 打磨概念稿：
   ```bash
   python3 pmem_art.py converge start --goal "UI概念稿：<屏幕类型+风格>" --module <ui.模块> [--scale medium|high]
   # 每轮：converge generate 生图，再 converge judge 审图，直到 >=9.6 或满 8 轮
   python3 pmem_art.py converge finish
   ```
3. **概念稿通过后才进入组件表**——不要在概念未锁定时散生按钮。

### Step 2：从概念抽取组件表（Component Sheets）
以概念稿为垫图/参考，在 **透明底** 上生成组件表（1~3 张 sheet），覆盖：
- **面板 / 边框 / 装饰条**（可九宫格拉伸）
- **按钮族**：至少 normal + pressed（最好含 hover / disabled）
- **进度条 / 血条**：空轨 + 满轨（或分段填充）
- **标签 / Tab**：选中 + 未选中
- **图标位 / 分隔线 / 角花** 等概念中出现或隐含的零件
同一概念参考下批量生成，保证木纹/螺栓/色板/光影角度一致。缺件时只补缺件，不要整套重开。

### Step 3：九宫格切线与清单（9-Slice + Manifest）
对每个可缩放件标注九宫格：四角固定、四边单向拉伸、中心双向拉伸。输出清单建议：
```
ui_kit_<name>/
├── concept.png
├── sheets/
├── elements/          # 透明 PNG 单件
├── manifest.json      # name / group / state / rect / nine_slice {l,r,t,b}
└── preview.html       # 可选：拼装预览
```
`manifest.json` 示例字段：`name`, `group`, `state`, `file`, `nine_slice: {left,right,top,bottom}`, `scalable: true|false`。

### Step 4：关键件二次收敛（可选但推荐）
对主面板、主按钮等核心件，若五维评分 `< 9.6`（重点查：中心拉伸区是否干净、转角是否形变、透明底毛边、状态族是否同系），再跑一轮 `converge generate` 局部重绘，然后 `converge judge` 审图。

### Step 5：沉淀记忆
```bash
python3 pmem_art.py ingest <concept或主面板路径> -p "UI kit <屏幕> 概念/主面板" --apply
python3 pmem_art.py feedback "UI套件色板与九宫格规范：<摘要>" --module <ui.模块> --kind art_decision
```

## 三、UI 专用五维评分侧重（满分 10.0，`>= 9.6` 合格）
1. 风格色板契合（2.5）— 与概念稿同材质同色板
2. 结构/九宫格合理性（2.5）— 中心区干净、角不糊、可拉伸
3. 光影材质完成度（2.0）
4. 红线与管线合规（1.5）— RGBA 透明底、分辨率、无脏边
5. 套件一致性 / 状态族完整（1.5）— normal/pressed 等同系，不「各画各的」

## 四、最终交付必须包含
1. 概念稿 + 组件表 + `elements/` + `manifest.json`（含九宫格）
2. 若跑了收敛：默认附上全轮次评分优劣总表（不足/改点）；只要终稿用 `--quiet`
3. 已写入 `.memory-art` 的 recipe / redline 路径


## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
