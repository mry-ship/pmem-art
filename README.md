# 🎨 pmem-art — 在 Cursor / Codex 里越画越准的个人美术积累记忆 & 闭环自评生图系统

> **怎么用**：装上就用，系统自己变强（静默自动驾驶）。日常只需画；偶尔一行「小提示」。

<p align="left">
  <img src="https://img.shields.io/badge/version-v0.12.0-0ea5e9?style=for-the-badge" alt="v0.12.0"/>
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/UX-Cursor%20对话%20%2B%20内置%20Skills-8b5cf6?style=for-the-badge" alt="Cursor-first + Skills"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-f59e0b?style=for-the-badge" alt="GPL-3.0"/>
</p>

> **核心定位**：个人美术 **静默自动驾驶记忆系统** — 装上就用，系统自己变强。  
> **一句话心智模型**：`画 → 偶尔一行「小提示」 → 后台自动反思/口味/知识 → 越用越好`（improve/coach/learn 为进阶 peek）。  
> 姊妹项目：[mry-ship/pmem](https://github.com/mry-ship/pmem)（代码工程研发记忆）。

📘 [画师手册 USER_MANUAL.md](./USER_MANUAL.md) · 🧠 [架构 ARCHITECTURE.md](./ARCHITECTURE.md) · 📈 [完整图文实测报告 benchmark-evolution-report.html](./benchmark-evolution-report.html) · 🖼️ [可视化图谱 art-atlas.html](./art-atlas.html) · ⚖️ [LICENSE](./LICENSE)

---

## 📊 实测基准报告（Benchmark Results：有记忆 vs 无记忆 & 冷启动 vs 热启动）

> 🔗 **完整图文演进报告（含 20 轮实测真图、五维雷达、记忆注入溯源）**：**[📈 点击查看 `benchmark-evolution-report.html`](./benchmark-evolution-report.html)**

我们在四大核心游戏美术域（**角色立绘 / 场景原画 / UI 九宫格弹窗 / 战斗刀光特效**）上进行了严苛的端到端实测对比，量化验证 **无记忆冷启动（No-Memory Baseline）**、**空项目自进化收敛（Cold-Start Self-Evolution）** 与 **挂载记忆库热启动（Warm-Start with Memory）** 的真实差距：

### 1️⃣ 表 1：空项目冷启动（Batch 1：从 0 记忆自迭代至 ≥9.5 收敛）— 无记忆首轮 vs 有记忆自进化收敛

| 实测任务 (模块) | 无记忆首轮 (R1) 综合分 & 五维明细 | R1 红线命中 | 自进化迭代轨迹 (`R1 → Rn`) | 有记忆收敛定稿分 & 五维明细 | 定稿红线 | 收敛轮次 | 净增提分 |
| :--- | :--- | :---: | :--- | :--- | :---: | :---: | :---: |
| **B1-T1 角色立绘**<br>`character.Astra` | **`7.00`**<br><small>构图`6.8` / 光影`7.2` / 色板`6.5` / 材质`7.0` / 工程`7.5`</small> | 2 处 | `7.00 → 8.40 → 9.10 →` **`9.60` ✅** | **`9.60`**<br><small>构图`9.6` / 光影`9.6` / 色板`9.7` / 材质`9.5` / 工程`9.6`</small> | **0 处** | **4 轮** | **`+2.60`** |
| **B1-T2 场景原画**<br>`scene.Celadon_Shrine` | **`6.70`**<br><small>构图`6.5` / 光影`6.8` / 色板`6.2` / 材质`6.8` / 工程`7.2`</small> | 3 处 | `6.70 → 8.20 → 9.00 →` **`9.55` ✅** | **`9.55`**<br><small>构图`9.5` / 光影`9.7` / 色板`9.6` / 材质`9.4` / 工程`9.6`</small> | **0 处** | **4 轮** | **`+2.85`** |
| **B1-T3 UI九宫格弹窗**<br>`ui.Dialog_Reward` | **`6.80`**<br><small>构图`7.0` / 光影`6.9` / 色板`6.8` / 材质`6.7` / 工程`6.6`</small> | 3 处 | `6.80 → 8.60 →` **`9.62` ✅** | **`9.62`**<br><small>构图`9.6` / 光影`9.5` / 色板`9.6` / 材质`9.6` / 工程`9.8`</small> | **0 处** | **3 轮** | **`+2.82`** |
| **B1-T4 战斗特效**<br>`vfx.Slash_Celadon` | **`7.10`**<br><small>构图`7.2` / 光影`7.3` / 色板`7.0` / 材质`7.1` / 工程`6.9`</small> | 2 处 | `7.10 → 8.70 →` **`9.56` ✅** | **`9.56`**<br><small>构图`9.5` / 光影`9.6` / 色板`9.6` / 材质`9.5` / 工程`9.6`</small> | **0 处** | **3 轮** | **`+2.46`** |
| **🏆 Batch 1 汇总均值** | **`6.90 / 10`**<br><small>无记忆直出普遍偏离项目色板与规格</small> | **共 10 处** | **全任务 100% 跨过 `≥9.5` 门槛** | **`9.58 / 10`**<br><small>五维全面跃升至主美签收级</small> | **0 处 (清零)** | **平均 `3.50 轮`**<br><small>(总计 14 轮)</small> | **`+2.68 分`**<br>**(`+38.8%`)** |

> 💡 **表 1 一句话结论**：在完全零记忆的空项目中，无记忆首轮直出均分仅 **`6.90 分`** 且频发 **10 处风格/规格红线**；通过 `pmem-art` 闭环自评与记忆实时写回，平均仅需 **`3.50 轮`** 即可将画质拉升至 **`9.58 分 (+38.8%)`** 并实现 **红线 100% 清零**。

---

### 2️⃣ 表 2：非空项目热启动（Batch 2：挂载已沉淀记忆库直出）— 无记忆冷启动 vs 有记忆热启动对比

| 核心评测维度 (Metric) | ❌ 无记忆冷启动 (Batch 1 基线) | ✅ 有记忆热启动 (Batch 2 挂载记忆库) | 🚀 提升幅度 / 收益结论 |
| :--- | :---: | :---: | :--- |
| **首轮直出均分 (First-Round Score)** | `6.90 / 10` | **`9.35 / 10`**<br><small>(`B2-T1`角色 `9.30`→R2 `9.68` · `B2-T2`场景 **`9.58`一轮直达** · `B2-T3` UI **`9.56`一轮直达** · `B2-T4`特效 `8.95`→R2 `9.62`)</small> | **`+2.45 分 (+35.5%)`**，首轮即逼近甚至直接跨过 `9.5` 签收线 |
| **达标 `≥9.5` 平均轮次 (Avg Rounds)** | `3.50 轮 / 任务` | **`1.50 轮 / 任务`**<br><small>(4 项任务中 **2 项首轮 R1 直接 ≥9.5 达标**)</small> | **收敛提速 `57.1%`（立省 `57.1%` 生图 Token 与时间开销）** |
| **4 项任务总生图轮次 (Total Rounds)** | `14 轮` | **`6 轮`** | **净省 `8 轮 (-57.1%)`** |
| **最终定稿均分 (Final Converged Score)** | `9.58 / 10` | **`9.61 / 10`** | 保持 **`>9.6` 主美级高水准稳定交付** |
| **热启动记忆命中率 (Warm-Start Hit Rate)** | `0% (0/4)` | **`100% (4/4 任务全命中)`** | 每次生图前自动精准召回对应模块红线、色板与配方 |
| **单任务平均挂载记忆数 (Memories Injected)** | `0.0 条` | **`11.2 条 / 任务`** | 自动组装 **项目专项红线/正例 + 跨项目通用美术知识卡** |
| **记忆置信度演进 (Memory Confidence)** | `0.19` | **`0.83`** | **置信度跃升 `+336.8%`**，高频验证规则权重自动置顶 |
| **历史红线复发次数 (Redline Recurrence)** | `10 次` | **`0 次（100% 免疫）`** | 赛博霓虹串色、九宫格中心花纹、头身比失调等历史旧病 **零复发** |

> 💡 **表 2 一句话结论**：一旦沉淀出项目专项记忆库，后续同类/衍生任务首轮直出均分从 **`6.90` 飙升至 `9.35 (+35.5%)`**，半数任务 **1 轮直达 `≥9.5`**，总生图轮次从 **14 轮锐减至 6 轮（立省 `57.1%` 算力与返工成本）**，且历史踩坑红线 **100% 终生免疫**。

---

### 3️⃣ 表 3：全周期记忆与知识资产沉淀总览（Overall Memory & Asset Accumulation）

| 资产与记忆维度 | 初始空项目 (Initial) | Batch 1 冷启动收敛后 | Batch 2 热启动演进后 | 沉淀机制与工程价值 |
| :--- | :---: | :---: | :---: | :--- |
| **📦 视觉模块覆盖 (Visual Modules)** | `6` | `10` | **`12`** | 自动派生角色/场景/UI/特效/动画/图标等细分模块契约 |
| **🧭 结构化专项记忆 (Structured Memories)** | `0 条` | `14 条` | **`21 条`** | 含 `style_redline` 红线、`recipe` 黄金配方、`visual_correction`、`asset_record` |
| **🌍 美术知识广度卡 (Knowledge Cards)** | `0 张` | `5 张私有 + 10 张共享` | **`8 张项目专项卡 + 10 张全局共享通用卡`** | **双层隔离**：项目私有画风锁死不串味，通用美术规律跨项目永久复用 |
| **🎨 审美偏好信号 (Taste Signals)** | `0 条` | `6 Kept / 5 Rejected` | **`11 条采纳偏好 (Kept) / 8 条禁用习惯 (Rejected)`** | 静默提取个人光影、色温、构图偏好，自动注入 Warm-Start |
| **🖼️ 图谱自动入库真图 (Atlas Images)** | `0 张` | `14 张` | **`23 张实测真图`** | **100% 自动携带中文结构化描述、Prompt 与轮次演进轨迹入库** |

> 💡 **表 3 一句话结论**：画师日常只需正常生图与随口反馈，系统即可在后台从 0 自动长出 **21 条结构化记忆 + 18 张双层知识卡 + 19 条审美口味信号 + 23 张带描述图谱资产**，真正把「一次性生图消耗」转化为「可复利的团队/个人美术资产库」。

---

## 🗂️ 双层记忆架构 & 项目命名专项库（支持直接拷贝 `.memory-art` 到新项目自动隔离建库）

`pmem-art` 采用 **「项目命名专项记忆库 + 全局跨项目通用共享库」** 双层架构，既保证不同项目画风 **100% 物理隔离不串味**，又支持直接把旧项目的 `.memory-art/` 文件夹拷贝到新项目继续演进：

1. **🏷️ 项目命名专项记忆库（`.memory-art/projects/<project-slug>/` · `layer_scope: "private"`）**：
   - 每个项目的专属记忆库都带有明确的项目标识（`project_id` / `project_name`，保存在 `.memory-art/active_project.json` 与 `.memory-art/projects/<project-slug>/library.json`）。
   - 存放仅属于该项目的模块树 (`modules.yaml`)、主美红线 (`style_redline`)、定稿配方 (`recipe`)、专属色板 HEX、个人口味 (`_profile/taste.json`) 与私有画风知识卡。
2. **📂 直接拷贝 `.memory-art` 文件夹到新项目自动隔离工作流（Copy-Folder Auto-Isolation）**：
   - 当你开启新项目 `ProjectB`，直接把旧项目 `ProjectA` 的整个 `.memory-art/` 文件夹拷贝到 `ProjectB/.memory-art/` 时：
   - 系统在首次运行任意指令（`init` / `load_project` / `converge` / `feedback` / `atlas`）时会自动检测到项目目录切换：
     1. **完整封存旧项目专项库**：将 `ProjectA` 的全部专项记忆完好无损地归档保留在 `.memory-art/projects/<project-a-slug>/` 中（一条不丢，可在 `art-atlas.html` 的 **「🗂️ 专项记忆库项目切换器」** 中随时点击回看历史项目演进）。
     2. **自动新建当前项目干净专项库**：为 `ProjectB` 自动创建 `.memory-art/projects/<project-b-slug>/` 并清空当前工作区的私有条目，确保旧项目的青瓷/赛博等私有画风 **绝不混入新项目的生图召回**！
3. **🌐 全局跨项目通用共享库（`~/.pmem-art/shared/` · `layer_scope: "shared"`）**：
   - 全局唯一一份，仅存放 **与具体画风无关的通用美术规律**（如头身比尺规、手部透视三段法、70/20/10 配色黄金比、大气透视、九宫格拉伸规范、VFX 能量衰减曲线）。
   - 任何新项目冷启动自动挂载；同模块召回时遵循 `rank_memory_entry` 严格优先级：**当前项目专项库 (`private`) > 全局共享通用库 (`shared`)**，历史归档项目专项库严格排除在召回之外。

---

## 🌟 亮点一：初始化自动注入 斜杠技能（Cursor / Claude Code / Codex 开箱即用）

运行 `python3 pmem_art.py init`（或在已有项目运行 `python3 pmem_art.py skills --install`）时，系统会自动把 **美术技能（含 improve/coach/learn；每项含简短别名）** 安装到：
- **Cursor**：`.cursor/skills/<name>/SKILL.md` + `.cursor/commands/<name>.md` + `.cursor/rules/pmem-art.mdc`
- **Claude Code**：`.claude/skills/<name>/SKILL.md` + `.claude/commands/<name>.md` + `CLAUDE.md`
- **Codex**：`.agents/skills/<name>/SKILL.md` + `AGENTS.md`

### 内置美术技能一览

| 斜杠指令 | 简短别名 | 核心能力 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | 🔥 **【强制 8轮 ≥9.5 收敛】** 通用生图（①纯文本 ②垫图先解构）。生1张→五维打分+挑不合理处→`<9.5`叠加修正继续→最多8轮达标即停或挑最高分→**全轮次评分总表** |
| **`/pmem-ui`** | **`/art-ui`** | 🕹️ **【强制 8轮 ≥9.5 收敛】** SpriteCook 式 UI Kit/HUD/九宫格：概念先行→透明组件表→九宫格+状态族；概念稿与关键件同样强制闭环 |
| **`/pmem-concept`** | **`/art-concept`** | 🎬 **【强制 8轮 ≥9.5 收敛】** **原画 / 概念图 / Key Art**（ZHO·FLUX 完整句 Prompt）— **与 `/pmem-draw` 同等强制闭环，禁止只生一张就交差** |
| **`/pmem-icon`** | **`/art-icon`** | ✳️ **【强制 8轮 ≥9.5 收敛】** jezweb 式一致化 SVG 图标集：style-spec→约5个一批→`preview.html`；关键单枚强制闭环打磨 |
| **`/pmem-style-lock`** | **`/art-style`** | 🎨 **样张一键提炼风格圣经与色板锁定**：丢入 1~3 张参考样张，自动提取主辅色 HEX、光影笔触与反例禁用词，写入项目记忆 |
| **`/pmem-critique`** | **`/art-check`** | 🔍 **单图/批量图主美级五维审稿挑刺**：对照项目已有红线与规格打分，指出不合理处并一键记入 `style_redline` |
| **`/pmem-variant`** | **`/art-variant`** | 🌿 **同角色跨画风分叉与表情/动作差分**：锁死角色核心人设锚点，派生水彩/Q版/像素子模块或序列帧差分 |
| **`/pmem-atlas`** | **`/art-map`** | 🗺️ **一键归档散图并刷新 `art-atlas.html` 可视化图谱** |
| **`/pmem-improve`** | **`/art-improve`** | 🧠 **【进阶 peek】** 自我迭代报告（日常 finish 已静默跑） |
| **`/pmem-coach`** | **`/art-coach`** | 🎓 **【进阶 peek】** 能力教练练习计划 |
| **`/pmem-learn`** | **`/art-learn`** | 🌍 **【进阶 peek】** 知识广度（finish 已静默 enqueue） |

---

## 🔥 重点详解：`/pmem-draw`（或 `/art-draw`）8轮 9.5分 闭环自评收敛生图

在 Cursor / Claude Code / Codex 对话框中直接输入，支持 **两种调用方式**：

### 用法 1：纯文字直接收敛生图
```text
/pmem-draw 生成一张东方青瓷水彩风格的阿斯特拉半身立绘，透明底
```

### 用法 2：丢入一张参考图 + 先解构再收敛生图
```text
/pmem-draw [拖入/附上参考图] 生成一张同画风但换成冰霜刀光特效的武器图标
```

### 它在后台自动跑的闭环流程（最多 8 轮，合格线 `>= 9.5 / 10.0`）

```text
[若有参考图] Step 0: 先深度解构丢进来的图（构图视角 / 主辅色HEX / 光影冷暖 / 笔触材质 / 头身结构）
      ↓
Step 1: 自动 search .memory-art 召回该模块历史红线 (style_redline) 与定稿配方 (recipe)
      ↓
Step 2: 进入自评收敛循环 (Round 1 .. 8)
   ├─ 1) 调用生图工具生成 1 张图
   ├─ 2) 亲自审图 + 五维严苛打分（风格色板2.5 / 结构透视2.5 / 光影材质2.0 / 红线合规1.5 / 意图还原1.5 = 10.0分）
   ├─ 3) 明确说出这张图【哪里合理】+【哪里不合理需要改】
   └─ 4) 判定：
         · 评分 >= 9.5  ──► ✅ 合格达标！立即停止循环，采用本张图
         · 评分 <  9.5 且未满 8 轮 ──► 🔄 不合格！把不合理处转成叠加修正指令并入下一轮 Prompt，继续生下一张
         · 满 8 轮仍 < 9.5 ──► 🏆 停止循环，从 1~8 轮里挑出【得分最高】的那张图作为最终结果
      ↓
Step 3: 输出【全阶段评分与优劣分析总表】+ 自动把胜出配方与踩坑红线写入 .memory-art
```

#### 最终自动生成的汇总表示例（由 `pmem_art.py converge finish --apply` 产出）

| 轮次 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮 | `.cursor/generated/r1.png` | **7.8**<br><small>风格1.9/结构1.8/光影1.6/合规1.3/还原1.2</small> | 青瓷白主色调准确 | 背景混入赛博紫光，头身比偏5.5头身幼态，左手手指粘连 | 叠加 `no neon purple, 7.5 heads tall, clear 5 fingers` | ❌ 未达标 |
| 第 2 轮 | `.cursor/generated/r2.png` | **8.9**<br><small>风格2.3/结构2.2/光影1.7/合规1.4/还原1.3</small> | 7.5头身修长比例恢复，霓虹紫已消除 | 左眼（画面右侧）黄铜星盘义眼漏画十字星芒，披风边缘略糊 | 叠加 `brass astrolabe monocle on left eye with crisp 4-point star glint` | ❌ 未达标 |
| 第 3 轮 | `.cursor/generated/r3.png` | **9.6**<br><small>风格2.5/结构2.4/光影1.9/合规1.4/还原1.4</small> | 青瓷白+墨蓝配比精准、7.5头身、左眼星盘义眼清晰、RGBA透明底干净 | 极细微衣摆暗部层次可接受 | 已达标，无需继续叠加 | 🏆 **胜出采用** |

---

## 🕹️ 亮点二：三大垂直生成技能（UI / 原画 / 图标）— 怎么用 & 原理

三个技能都挂同一套 **`converge`：最多 8 轮 · 合格线 `≥ 9.5` · 未达标叠加修正 · 满 8 轮挑最高分 · 输出评分总表 · 写入 `.memory-art`**。  
差别只在「领域流水线」：UI 走概念→组件→九宫格；原画走 FLUX 完整句；图标走 style-spec 批量一致化。

| 指令 | 别名 | 对标 | 一句话 |
| :--- | :--- | :--- | :--- |
| **`/pmem-ui`** | `/art-ui` | SpriteCook | 概念先行 → 整套 HUD/组件表 → 九宫格+状态族 → **强制 8轮≥9.5** |
| **`/pmem-concept`** | `/art-concept` | ZHO / Yolain / Comfy-FLUX | **原画 / Key Art** · 完整句 Prompt → **强制 8轮≥9.5**（禁止只生一张） |
| **`/pmem-icon`** | `/art-icon` | jezweb | 统一 style-spec → 批量图标集（SVG/`preview.html`）→ 关键枚 **强制 8轮≥9.5** |

---

### 1️⃣ `/pmem-ui`（`/art-ui`）— UI Kit / HUD / 九宫格整套

#### 怎么用
```text
# 纯文字：从零做一整套主菜单
/pmem-ui 生成一套青瓷幻想风主菜单：可九宫格拉伸的面板，按钮含 normal/pressed/disabled

# 纯文字：HUD
/art-ui 做一套蒸汽朋克战斗 HUD（血条空满态、技能槽、小地图框），透明底可切图

# 垫图：已有概念稿，拆成可复用零件
/pmem-ui [拖入概念图] 按这张概念拆出：主面板九宫格、主按钮四态、进度条空/满、Tab 选中/未选中
```

#### 原理（为什么这样跑）
1. **记忆先行**：`search --module ui.*` 召回该 UI 模块历史红线（脏边、中心拉伸区花纹、霓虹串色等）与定稿配方。  
2. **概念先行（SpriteCook 核心）**：先收敛出 **1 张整屏概念稿**（统一材质/色板/光影），**禁止**各控件零散各生一张再硬拼。  
3. **组件表**：以概念稿为垫图，在透明底上生成 1~3 张组件 sheet（面板、按钮族、进度条、Tab、角花…）。  
4. **九宫格 + 状态族**：给可拉伸件标 `nine_slice {l,r,t,b}`；按钮至少 normal/pressed（最好含 hover/disabled）。输出 `elements/` + `manifest.json`。  
5. **强制 8轮 ≥9.5**：概念稿与主面板/主按钮等关键件走 `converge`——生 1 张 → 五维打分+挑不合理处 → `<9.5` 叠加修正 → 最多 8 轮或挑最高分 → 评分总表写入记忆。

---

### 2️⃣ `/pmem-concept`（`/art-concept`）— 原画 / 概念图 / Key Art

#### 怎么用
```text
# 纯文字：主视觉 / 原画
/pmem-concept 画一张东方青瓷废土的主视觉 Key Art，宽幅海报，电影感侧逆光

# 纯文字：场景气氛图
/art-concept 生成一张浮空遗迹黄昏气氛概念图，青瓷白+墨蓝+鎏金，叙事构图

# 垫图：先解构参考再收敛出同氛围原画
/pmem-concept [拖入参考图] 保持这种构图与色板，画一张同世界观的角色登场 Key Art
```

#### 原理（为什么这样跑）
1. **与 `/pmem-draw` 同等强制闭环**：原画也是 **最多 8 轮 · `≥9.5` 才合格 · 满 8 轮挑最高分 · 必须出评分优劣总表** —— **禁止只生一张就交差**。  
2. **记忆先行**：`search` 召回 `scene.*` / `character.*` / `brand.*` 的红线、定稿与色板，避免重犯「太赛博 / 脏暗 / 比例崩」。  
3. **FLUX 式完整句 Prompt（ZHO / Yolain）**：用自然语言完整句，**主体与动作靠前**；几乎无有效负向词，把「不要霓虹紫」写成「干净的青瓷白与墨蓝，无霓虹」。  
4. **垫图模式**：若丢入参考图 → Step0 解构构图/HEX/光影/笔触 → 再进入 8 轮收敛。  
5. **沉淀**：胜出图进 `recipe`，迭代中的硬伤进 `style_redline`，下次原画起点更高。

---

### 3️⃣ `/pmem-icon`（`/art-icon`）— 一致化图标集 / SVG

#### 怎么用
```text
# 纯文字：整套导航 + 业务图标（SVG）
/pmem-icon 给本项目做一套 24px Clean 预设导航+背包图标（SVG），输出 style-spec.json 与 preview.html

# 纯文字：指定图标名
/art-icon home settings inventory craft map quest

# 垫图 / 品牌样张：锁风格后再批量
/pmem-icon [拖入品牌样张或现有图标] 按这个线宽与圆角，补齐通信类图标：phone email location
```

#### 原理（为什么这样跑）
1. **先锁 style-spec（jezweb 核心）**：选定 Clean/Sharp/Soft/Minimal/Bold，写死 grid、stroke、linecap、linejoin、padding —— **整套共用一份规格**，避免「每张各画各的」。  
2. **SVG 硬规则**：统一 `viewBox`、只用 `currentColor`、根节点 stroke 属性一致、光学居中与视觉重量平衡。  
3. **分批生成（约 5 个一批）**：每批做一致性审查（线宽漂移、圆角混用、偏轻偏重、贴边）。交付 `icons/*.svg` + `style-spec.json` + `preview.html`。  
4. **强制 8轮 ≥9.5**：用户点名「这枚不对」或审查不通过的关键图标，走同一套 `converge` 闭环打磨。  
5. **记忆**：把 style-spec 摘要写入 `art_decision`，翻车点写入 `style_redline`，下套图标不跑偏。

---

## 🚀 亮点三：静默自动驾驶（Whisper Autopilot · v0.12）

**装上就用，系统自己变强。** 过程几乎不用你察觉——收敛结束与高信号反馈后，后台自动写反思、更新口味、强化配方/红线、悄悄排队知识建议；你最多看到一行「小提示」。

```text
「小提示」下次注意：头身比
「小提示」已记住：不要过曝高光
```

| 能力 | 日常（默认） | 进阶 peek（可选） |
| :--- | :--- | :--- |
| **静默自动驾驶** | `converge finish --apply` / 高信号 `feedback` 自动跑 | — |
| **小提示** | 每会话最多 1 条；不刷屏 | `--verbose` 看全量报告 |
| **Warm-Start / 8×≥9.5** | 照常强制闭环 | `--mode fast` 可 fast-track |
| **自我迭代 / 教练 / 广度** | 后台已跑 | `/pmem-improve` · `/pmem-coach` · `/pmem-learn` · `progress` |

### 个人进步（想看再看）
`python3 pmem_art.py progress` 看近 7/30 胜出分、短板是否下降、知识卡是否变多——**不是日常必跑**。

---

## 💬 亮点四：平时随口评一句，记忆自动长大（无需手写 YAML）


除了用 `/pmem-draw` 自动收敛，你日常在 Cursor 对话里看图后随口说的每一句中文评价，都会自动沉淀进 `.memory-art/`：

| 你在对话里说 | 系统自动记住的记忆类型 | 下次生图时的效果 |
| :--- | :--- | :--- |
| **「太赛博了，别这样画」** / **「头太大」** | `style_redline`（红线） | 下次自动塞进禁止项，绝不重犯 |
| **「这版留着」** / **「就这个」** | `recipe`（定稿锚点） | 下次优先沿用这张的构图、色板与方向 |
| **「换成水彩」** / **「改成 Q 版」** | `visual_correction`（修正 + 画风分叉） | 自动分叉到 `.Watercolor` / `.Chibi` 子模块，与正比立绘隔离 |
| **「以后都用青瓷白+墨蓝，别霓虹」** | `art_decision`（审美拍板） | 升级为模块/全局长期定调 |

---

## ⚡ 30 秒安装接入（装上就用，系统自己变强）

### 1. 新项目 / 空项目冷启动
```bash
python3 pmem_art.py init --name "我的项目"
python3 pmem_art.py bootstrap --mode young --apply
```
> 自动建好 `.memory-art/`、`assets/` 与技能。之后日常只需画；finish/feedback 后**静默自动驾驶**，improve/coach/learn 为进阶 peek。

### 2. 已有资产的老项目无损挂载
```bash
python3 pmem_art.py bootstrap --mode legacy --roots Art assets
python3 pmem_art.py accept --all
python3 pmem_art.py skills --install
```
> 老项目文件**绝不自动搬家**；一键装好技能后即可在 Cursor 对话中越画越准。

---

## 🛠️ 核心命令速查（主要由 Agent 自动调用，你也可手动运行）

```bash
# 列出或安装 Cursor / Claude Code / Codex 内置技能
python3 pmem_art.py skills --list
python3 pmem_art.py skills --install

# 闭环收敛（Warm-Start；默认 quality=完整8×≥9.5；--mode fast 可 fast-track）
python3 pmem_art.py converge start --goal "青瓷风阿斯特拉立绘" --module character.Astra
python3 pmem_art.py converge start --goal "草稿预览" -m character.Astra --mode fast --draft
python3 pmem_art.py converge round --round 1 --image r1.png --score 8.2 --strengths "..." --defects "头身偏大" --next-fix "..."
python3 pmem_art.py converge finish --apply          # 静默：沉淀+autopilot+一行小提示
python3 pmem_art.py converge finish --apply --verbose # 全量 Markdown 报告

# 进阶 peek（日常不必跑）
python3 pmem_art.py improve run
python3 pmem_art.py progress
python3 pmem_art.py taste show
python3 pmem_art.py coach
python3 pmem_art.py learn suggest
python3 pmem_art.py learn accept --all

# 自然语言反馈一键写记忆（同时强化口味+知识卡）
python3 pmem_art.py feedback "太赛博了，别这样画" -m character.Astra -a r1.png
python3 pmem_art.py note "这版留着" -m character.Astra -a r3.png

# 生图前检索记忆 & 新图后台多信号分类归档
python3 pmem_art.py search -m character.Astra
python3 pmem_art.py ingest .cursor/generated/r3.png -p "角色Astra 立绘" --apply
```

详细教程请查阅 📘 **[画师手册 USER_MANUAL.md](./USER_MANUAL.md)**。

---

## ⚖️ License

[GNU GPL v3.0](./LICENSE) · 与 [mry-ship/pmem](https://github.com/mry-ship/pmem) 一致。
