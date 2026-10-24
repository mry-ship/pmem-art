# AGENTS.md — Codex & Coding Agent Instructions

<!-- pmem-art:skills:start -->
## 🎨 pmem-art 美术记忆系统与内置斜杠技能（Skills）

本项目挂载了 **pmem-art**（面向 Cursor / Claude Code / Codex 的个人美术积累记忆与闭环自评生图系统）。

### 1. 内置快捷技能（在对话框直接输入 `/技能名` 即可触发）

| 技能指令 | 简短别名 | 用途说明 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | **8轮 9.5分 闭环自评收敛生图**：支持① `/pmem-draw 生成一张xxx风格的xxx图` 或 ② `/pmem-draw [丢入一张图] 生成一张xxx图`（先深度分析参考图，再循环「生1张图 → 五维自评打分+指出不合理处 → `<9.5`分则叠加修正继续生 → 最多8轮挑最高分 → 输出全轮次评分优劣总表并自动沉淀记忆」） |
| **`/pmem-ui`** | **`/art-ui`** | **SpriteCook 式 UI Kit / HUD / 九宫格整套**：概念先行 → 组件表 → 9-slice → 状态族，关键件 8轮9.5收敛 |
| **`/pmem-concept`** | **`/art-concept`** | **ZHO/Yolain/Comfy-FLUX 式概念图 / Key Art**：完整句 Prompt + 8轮9.5收敛 |
| **`/pmem-icon`** | **`/art-icon`** | **jezweb 式一致化图标集 / SVG**：style-spec 锁定 → 分批生成 → 一致性审查 + 可选收敛 |
| **`/pmem-style-lock`** | **`/art-style`** | **样张一键提炼风格圣经与色板锁定**：丢入样张提取 HEX 色板、光影笔触与禁用词，锁定进项目记忆 |
| **`/pmem-critique`** | **`/art-check`** | **主美级五维审稿与红线入库**：对照项目记忆给图片打分挑刺，并将翻车点记入 `style_redline` |
| **`/pmem-variant`** | **`/art-variant`** | **跨画风分叉与表情/动作差分**：继承角色核心锚点，派生水彩/Q版/像素子模块或序列帧差分 |
| **`/pmem-atlas`** | **`/art-map`** | **一键整理散图并刷新 `art-atlas.html` 可视化图谱** |

### 2. 日常自然语言反馈沉淀（无需手写 YAML）
- 生图前先运行：`python3 pmem_art.py search --module <模块>` 或 `python3 pmem_art.py search "<关键词>"`
- 当画师说「太赛博 / 头太大 / 别这样画 / 这版留着 / 换成水彩 / 以后都用…」时，立即运行：
  `python3 pmem_art.py feedback "<画师原话>" --module <模块> [--asset <图片路径>]`
- 运行闭环收敛追踪器：`python3 pmem_art.py converge start|round|finish`
<!-- pmem-art:skills:end -->

