# 🎨 pmem-art — 在 Cursor / Codex 里越画越准的个人美术积累记忆 & 闭环自评生图系统

<p align="left">
  <img src="https://img.shields.io/badge/version-v0.10.0-0ea5e9?style=for-the-badge" alt="v0.9.0"/>
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/UX-Cursor%20对话%20%2B%20内置%20Skills-8b5cf6?style=for-the-badge" alt="Cursor-first + Skills"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-f59e0b?style=for-the-badge" alt="GPL-3.0"/>
</p>

> **核心定位**：你在同一个项目（画风基线已定）里用 Cursor / Claude Code / Codex 反复生图、改图时的 **个人美术积累记忆 + 8轮 9.5分 闭环自评收敛生图技能**。  
> **一句话心智模型**：`生图 → 自评挑刺或你说一句哪里不对/这版留着 → 记忆自动变长 → 下次生图更准`。  
> 姊妹项目：[mry-ship/pmem](https://github.com/mry-ship/pmem)（代码工程研发记忆）。

📘 [画师手册 USER_MANUAL.md](./USER_MANUAL.md) · 🧠 [架构 ARCHITECTURE.md](./ARCHITECTURE.md) · ⚖️ [LICENSE](./LICENSE) · 🖼️ [可选回看 art-atlas.html](./art-atlas.html)

---

## 🌟 亮点一：初始化自动注入 8 大斜杠技能（Cursor / Claude Code / Codex 开箱即用）

运行 `python3 pmem_art.py init`（或在已有项目运行 `python3 pmem_art.py skills --install`）时，系统会自动把 **8 大美术技能（含简短别名共 16 个 `/` 斜杠入口）** 安装到：
- **Cursor**：`.cursor/skills/<name>/SKILL.md` + `.cursor/commands/<name>.md` + `.cursor/rules/pmem-art.mdc`
- **Claude Code**：`.claude/skills/<name>/SKILL.md` + `.claude/commands/<name>.md` + `CLAUDE.md`
- **Codex**：`.agents/skills/<name>/SKILL.md` + `AGENTS.md`

### 8 大内置美术技能一览

| 斜杠指令 | 简短别名 | 核心能力 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | 🔥 **8轮 9.5分 闭环自评收敛生图**（支持①纯文本指令生图；②**丢入参考图先深度分析再生图**。每次生1张 → 五维严苛自评打分+说出不合理处 → `<9.5`分自动叠加修正继续生 → 最多8轮达标即停或挑全阶段最高分 → 输出全轮次评分优劣总表并自动沉淀记忆） |
| **`/pmem-ui`** | **`/art-ui`** | 🕹️ **SpriteCook 式 UI Kit / HUD / 九宫格整套**：概念先行 → 透明组件表 → 九宫格切线与状态族（normal/pressed…）→ 关键件 8轮9.5收敛 |
| **`/pmem-concept`** | **`/art-concept`** | 🎬 **ZHO / Yolain / Comfy-FLUX 式概念图 / Key Art**：完整自然语言句 Prompt（主体优先、正向写排斥项）+ 8轮9.5收敛 |
| **`/pmem-icon`** | **`/art-icon`** | ✳️ **jezweb 式一致化图标集 / SVG**：先锁 style-spec（stroke/圆角/viewBox）→ 约5个一批生成 → 一致性审查 + `preview.html`；单枚可收敛 |
| **`/pmem-style-lock`** | **`/art-style`** | 🎨 **样张一键提炼风格圣经与色板锁定**：丢入 1~3 张参考样张，自动提取主辅色 HEX、光影笔触与反例禁用词，写入项目记忆 |
| **`/pmem-critique`** | **`/art-check`** | 🔍 **单图/批量图主美级五维审稿挑刺**：对照项目已有红线与规格打分，指出不合理处并一键记入 `style_redline` |
| **`/pmem-variant`** | **`/art-variant`** | 🌿 **同角色跨画风分叉与表情/动作差分**：锁死角色核心人设锚点，派生水彩/Q版/像素子模块或序列帧差分 |
| **`/pmem-atlas`** | **`/art-map`** | 🗺️ **一键归档散图并刷新 `art-atlas.html` 可视化图谱** |

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

## 🕹️ 亮点二：三大垂直生成技能（UI / 概念图 / 图标集）

均挂载同一套 **`converge` 8轮 `>=9.5` 自评收敛引擎**，只是流水线按业界最佳实践特化：

| 指令 | 对标思路 | 一句话流程 |
| :--- | :--- | :--- |
| **`/pmem-ui`** `/art-ui` | [SpriteCook UI Kit](https://www.spritecook.ai/docs/ui-kit) | 先锁整屏概念 → 从概念抽透明组件表 → 标九宫格与状态族 → 关键件收敛 |
| **`/pmem-concept`** `/art-concept` | ZHO Comfy-FLUX / Yolain 提示法 | 完整句 Prompt（主体靠前、正向写「不要什么」）→ 概念图/Key Art 收敛 |
| **`/pmem-icon`** `/art-icon` | [jezweb icon-set-generator](https://github.com/jezweb/claude-skills) | 定 style-spec → 分批 SVG（currentColor + 统一 viewBox/stroke）→ preview.html |

```text
/pmem-ui 生成一套青瓷幻想风的主菜单：面板可九宫格拉伸，按钮含 normal/pressed
/pmem-concept 画一张东方青瓷废土的主视觉 Key Art，宽幅海报
/pmem-icon 给本项目做一套 24px Clean 预设导航+背包图标（SVG）
```

---

## 💬 亮点三：平时随口评一句，记忆自动长大（无需手写 YAML）

除了用 `/pmem-draw` 自动收敛，你日常在 Cursor 对话里看图后随口说的每一句中文评价，都会自动沉淀进 `.memory-art/`：

| 你在对话里说 | 系统自动记住的记忆类型 | 下次生图时的效果 |
| :--- | :--- | :--- |
| **「太赛博了，别这样画」** / **「头太大」** | `style_redline`（红线） | 下次自动塞进禁止项，绝不重犯 |
| **「这版留着」** / **「就这个」** | `recipe`（定稿锚点） | 下次优先沿用这张的构图、色板与方向 |
| **「换成水彩」** / **「改成 Q 版」** | `visual_correction`（修正 + 画风分叉） | 自动分叉到 `.Watercolor` / `.Chibi` 子模块，与正比立绘隔离 |
| **「以后都用青瓷白+墨蓝，别霓虹」** | `art_decision`（审美拍板） | 升级为模块/全局长期定调 |

---

## ⚡ 30 秒安装接入

### 1. 新项目 / 空项目冷启动
```bash
python3 pmem_art.py init --name "我的项目"
python3 pmem_art.py bootstrap --mode young --apply
```
> 自动建好 `.memory-art/`、`assets/` 六大目录，并把 `/pmem-draw` / `/pmem-ui` / `/pmem-concept` / `/pmem-icon` 等 8 大技能装进 `.cursor/`、`.claude/`、`.agents/`。

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

# /pmem-draw 闭环收敛追踪器（最多8轮，>=9.5达标或挑最高分，输出总表并写记忆）
python3 pmem_art.py converge start --goal "青瓷风阿斯特拉立绘" --module character.Astra [--ref-image ref.png --ref-analysis "..."]
python3 pmem_art.py converge round --round 1 --image r1.png --score 8.2 --strengths "..." --defects "..." --next-fix "..."
python3 pmem_art.py converge finish --apply

# 自然语言反馈一键写记忆（无需手写 YAML）
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
