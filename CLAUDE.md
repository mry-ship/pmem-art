# CLAUDE.md — Project Instructions

<!-- pmem-art:skills:start -->
## 🎨 pmem-art 美术记忆系统与内置斜杠技能（Skills）

本项目挂载了 **pmem-art**（面向 Cursor / Claude Code / Codex 的个人美术积累记忆与闭环自评生图系统）。

### 1. 内置快捷技能（在对话框直接输入 `/技能名` 即可触发）

| 技能指令 | 简短别名 | 用途说明 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | **【强制 8轮 ≥9.6 收敛】** 通用生图：纯文本或垫图 → 生1张→打分挑刺→展示不足/改点→`<9.6`叠加修正→满8轮挑最高分→评分履历可见 |
| **`/pmem-ui`** | **`/art-ui`** | **【强制 8轮 ≥9.6 收敛】** SpriteCook 式 UI Kit/HUD/九宫格：概念先行→组件表→9-slice→状态族 |
| **`/pmem-concept`** | **`/art-concept`** | **【强制 8轮 ≥9.6 收敛】** 原画/概念图/Key Art（ZHO·FLUX 完整句 Prompt）— **与 draw 同等强制闭环，禁止只生一张** |
| **`/pmem-icon`** | **`/art-icon`** | **【强制 8轮 ≥9.6 收敛】** jezweb 式一致化 SVG 图标集：style-spec→分批→preview；关键枚强制收敛 |
| **`/pmem-style-lock`** | **`/art-style`** | **样张一键提炼风格圣经与色板锁定**：丢入样张提取 HEX 色板、光影笔触与禁用词，锁定进项目记忆 |
| **`/pmem-critique`** | **`/art-check`** | **主美级五维审稿与红线入库**：对照项目记忆给图片打分挑刺，并将翻车点记入 `style_redline` |
| **`/pmem-variant`** | **`/art-variant`** | **跨画风分叉与表情/动作差分**：继承角色核心锚点，派生水彩/Q版/像素子模块或序列帧差分 |
| **`/pmem-atlas`** | **`/art-map`** | **一键整理散图并刷新 `art-atlas.html` 可视化图谱** |
| **`/pmem-improve`** | **`/art-improve`** | **【进阶 peek】** 自我迭代报告（日常 finish 已静默跑） |
| **`/pmem-coach`** | **`/art-coach`** | **【进阶 peek】** 能力教练练习计划 |
| **`/pmem-learn`** | **`/art-learn`** | **【进阶 peek】** 知识广度建议（finish 已静默 enqueue） |
| **`/pmem-lens-propose`** | **`/art-lens`** | **具象镜头包提案**：生图前基于参考图给 4 套机位/光影/道具包，点选后再进收敛 |
| **`/pmem-clone-image`** | **`/art-clone`** | **【强制 8轮 ≥9.6 收敛】** ~95% 锁参考画风克隆到新题材（含角色双眼/UI双层描边硬门禁） |
| **`/pmem-merge-ladder`** | **`/art-ladder`** | **【强制 8轮 ≥9.6 收敛】** Merge-2 棋盘 L1–L8 整梯同框生成与切格审计 |

### 2. 评分履历可见 · 记忆静默写入（默认）
- 闭环每轮须向用户展示：五维分、不足、下一轮改点；`converge finish` 默认打印全轮评分履历并写记忆（`--no-apply` 可跳过；只要终稿加 `--quiet`）。
- `finish` / 高信号 `feedback` 后仍自动写反思、更新 taste、强化 recipe/红线、悄悄排队 learn——**不要**旁白记忆写入；最多转述一行「小提示」。
- 教练 / 广度报告用进阶技能 `/pmem-improve` · `/pmem-coach` · `/pmem-learn`。

### 3. 日常自然语言反馈沉淀（无需手写 YAML）
- 生图前先运行：`python3 pmem_art.py search --module <模块>` 或 `python3 pmem_art.py search "<关键词>"`
- 当画师说「太赛博 / 头太大 / 别这样画 / 这版留着 / 换成水彩 / 以后都用…」时，立即运行：
  `python3 pmem_art.py feedback "<画师原话>" --module <模块> [--asset <图片路径>]`
- 运行闭环收敛追踪器：`python3 pmem_art.py converge start`，然后每轮 `converge generate` 与 `converge judge`，最后 `converge finish`（默认打印评分履历）
<!-- pmem-art:skills:end -->

