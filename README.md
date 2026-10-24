# 🎨 pmem-art — 面向美术团队与 AI 美术 Agent 的插拔式视觉记忆、红线防翻车与多信号归类图谱系统

<p align="left">
  <img src="https://img.shields.io/badge/version-v0.7.0-0ea5e9?style=for-the-badge" alt="Version v0.7.0"/>
  <img src="https://img.shields.io/badge/python-%3E%3D3.10-3776ab?style=for-the-badge&logo=python&logoColor=white" alt="Python >=3.10"/>
  <img src="https://img.shields.io/badge/dependencies-Zero%20(Stdlib%20Only)-10b981?style=for-the-badge" alt="Zero Dependencies"/>
  <img src="https://img.shields.io/badge/agent-Cursor%20%7C%20Claude%20Code%20%7C%20Codex-8b5cf6?style=for-the-badge" alt="AI Agents"/>
  <img src="https://img.shields.io/badge/license-GPL--3.0-f59e0b?style=for-the-badge" alt="License GPL-3.0"/>
</p>

> **与 [`mry-ship/pmem`](https://github.com/mry-ship/pmem) 一脉相承的美术姊妹系统**。
> `pmem` 解决的是代码工程中 AI Agent 跨会话遗忘、重复踩坑与模块边界失控；**`pmem-art`** 则专为 **游戏与数字内容美术管线（2D 原画/立绘、UI 九宫格切图、场景气氛图、VFX 序列帧、Spine/Live2D 骨骼动画）** 以及 **AI 生图工作流（Cursor GenerateImage / ComfyUI / Flux / Stable Diffusion / Midjourney）** 打造——提供**可随 Git 入库的视觉记忆、主美红线闸门、多信号自动分类扩模块、像素级管线质检与单文件交互式 HTML 图谱工作台**。

📖 **[完整使用手册 (USER_MANUAL.md)](./USER_MANUAL.md)** · 🧠 **[深度架构设计文档 (ARCHITECTURE.md)](./ARCHITECTURE.md)** · 🎨 **[交互式美术图谱工作台 (art-atlas.html)](./art-atlas.html)** · ⚖️ **[开源许可证 (LICENSE)](./LICENSE)**

---

## 🎯 为什么要做 `pmem-art`？（解决四大美术与 AI 生图核心痛点）

在用 Cursor / ComfyUI / 多画师协作推进游戏或视觉项目时，团队往往会反复撞上四座大山：

| 传统痛点 | 后果 | `pmem-art` 的解决方案 |
| :--- | :--- | :--- |
| **1. 主美审稿红线跨会话失忆** | 上周刚打回过「赛博霓虹紫溢色」「Q版5头身比例」「九宫格中心画圆花纹拉伸变形」，换个会话 AI 或外包又犯一模一样的错。 | **`style_redline` 正反例视觉锚点 + 生图前强制闸门**：把打回废案（❌ Don't）与定稿基准图（✅ Do）绑定 SHA-256 哈希写入模块记忆，AI 生图前自动召回。 |
| **2. Cursor 持续生图到处乱放、无法归类** | 在 Cursor 里陆陆续续生成了几十张角色、不同画风概念图、序列帧、UI 弹窗，全堆在临时目录或乱取名，模块表跟不上。 | **四信号融合 `classify` + 自动扩模块 `ingest`**：综合「路径词 + Prompt 语义 + PNG 宽高比/Alpha/序列帧网格检测 + 已有模块继承」，高置信度自动建模块并归位，低置信度进 `misc.*` 候选绝不乱塞。 |
| **3. AI 抽卡配方不可复现** | 某张立绘效果极好，但过了三天没人记得用的是哪个底模、LoRA 权重、Seed、ControlNet 和负向词。 | **`recipe` 配方记忆 + PNG `tEXt` 元数据核对**：结构化沉淀 Checkpoint / LoRA / Seed / 正负向词 / ComfyUI 节点 JSON，在图谱工作台一键复制。 |
| **4. 进引擎前漏检透明底、尺寸与九宫格** | 画师或 AI 导出的 UI 漏抠 Alpha 变黑底、尺寸非 2 的幂次、序列帧未对齐、改了图却没同步文档。 | **`validate` / `doctor` 像素级管线质检 + Stale 过期检测**：零依赖直接解析 PNG IHDR / Alpha / 边缘安全留白与 SHA-256 锚点，违规即时拦截。 |

---

## ⚡ 30 秒极速上手

### 1️⃣ 双击体验可视化美术图谱工作台（零安装）

无需启动任何后端服务、无需安装第三方依赖，直接在 Finder / 资源管理器中双击打开仓库根目录下的 **`art-atlas.html`**，即可交互式体验：
- 🖼️ **按模块与画风分层的瀑布流画廊**（支持无极缩放缩略图，锚点图 ⚓ / 已验收 ✅ / 废案红线 ❌ 一目了然）
- 🏁 **四种专业美术查图画布底色一键切换**（棋盘格透明底 / 深灰暗房底 / 宣纸亮白底 / 实机夜色环境底，专治漏去背与白边黑边）
- 🚫 **正反例红线 Do vs. Don't 交互式拖动滑杆对比**（像素级比对为什么被打回 vs 为什么通过）
- 📐 **UI 九宫格切线（`[48, 48, 48, 48]` px）与安全留白框实时叠加**
- 🧪 **AI 生图配方工作台**（一键复制 Positive / Negative Prompt、ComfyUI JSON 与 Agent 上下文）

### 2️⃣ 命令行三步跑通（仅需 Python ≥ 3.10 标准库）

```bash
# 克隆仓库
git clone https://github.com/mry-ship/pmem-art.git
cd pmem-art

# 1. 查看所有美术模块、资产计数、红线数与健康状态
python3 pmem_art.py list

# 2. 按模块检索生图前必读上下文（自动向上继承父模块红线 + 全局色彩圣经）
python3 pmem_art.py search --module character.Astra.Expressions

# 3. 运行全项目管线规格与 Stale 过期体检，并重新编译 HTML 图谱
python3 pmem_art.py doctor
python3 pmem_art.py atlas
```

---

## 🚀 三种项目接入模式（从空项目、老项目到 Cursor 持续生图）

`pmem-art` 拒绝「全自动黑盒乱改你磁盘」的伪智能，也拒绝「全靠手写 YAML」的高门槛，提供三套清晰可控的生命周期工作流：

### 模式 A：空项目 / 刚立项冷启动（`init` + `bootstrap --mode young`）

适合刚建好仓库、还没有多少美术图的项目。先搭好 6 大领域脚手架目录与 `scaffold` 引导模块，后续进图自动生长：

```bash
python3 pmem_art.py --root /path/to/your-game init --name "MyGame"
python3 pmem_art.py --root /path/to/your-game bootstrap --mode young --apply
```
- **保障机制**：自动创建 `assets/{brand,character,scene,ui,vfx,anim}/` 与 `.cursor/rules/pmem-art.mdc`；年轻项目默认开启 `bootstrap.auto_place: true`，配合 `ingest` 自动扩充模块并归位资产。

### 模式 B：已有大量历史资产的老项目接入（`bootstrap --mode legacy`）

适合已经开发数月、资产散落在 `Art/`、`Content/`、`assets/` 等不同目录的存量项目：

```bash
# 1. 扫描现有目录树，聚类生成候选模块与诊断报告（绝不自动移动任何文件！）
python3 pmem_art.py bootstrap --mode legacy --roots Art Content assets

# 2. 查看提议的候选模块与置信度，一键确认激活
python3 pmem_art.py candidates
python3 pmem_art.py accept --all

# 3. 预览孤儿资产归位计划（dry-run），确认无误后再加 --apply 执行移动
python3 pmem_art.py place --plan-orphans
python3 pmem_art.py place --plan-orphans --apply
```
- **保障机制**：`never_auto_move: true` 默认锁死；`accept --all` 只提升有真实资产的候选模块，绝不误把空的通配脚手架转正；生成 `.memory-art/LEGACY_BOOTSTRAP_REPORT.md` 供主美审阅。

### 模式 C：在 Cursor 中持续生图、多画风分叉与自动扩模块（`classify` + `ingest`）

当你在 Cursor 中不断调用生图工具产出角色立绘、不同画风概念图（水彩 / Q版 / 赛博）、UI 九宫格、序列帧特效时：

```bash
# 仅分类预览：输出建议模块、置信度、画风分叉、图像特征与四维信号得分（JSON）
python3 pmem_art.py classify .cursor/generated/new_img.png -p "角色Astra 水彩 概念图"

# 分类 + 自动在 modules.yaml 增量注册新模块 + 移动归位 + 生成资产台账记忆桩
python3 pmem_art.py ingest .cursor/generated/new_img.png -p "角色Astra 水彩 概念图" --apply

# 批量扫描所有监听目录（.cursor/generated, assets 等）中的新图
python3 pmem_art.py classify-watch --apply
```

#### 🧠 四信号融合分类器（Multi-Signal Classifier）如何工作？
1. **Prompt 语义信号（权重 0.35）**：识别中英文领域词（`角色/立绘/三视图`、`UI/九宫格/弹窗`、`VFX/刀光/序列帧`、`场景/气氛图`、`Spine/骨骼`）与画风词（`水彩 Watercolor`、`Q版 Chibi`、`像素 Pixel`、`赛博 Cyber`），并遵循「显式角色词优先于概念图泛词」消歧规则。
2. **路径与文件名信号（权重 0.25）**：自动剥离 `cursor_`、`gen_`、`v1`、`4f`、`9slice` 等前缀/后缀噪音，优先提取 `FrostSlash`、`JadeHarbor`、`Astra` 等实体名。
3. **图像物理特征信号（权重 0.25）**：直接读取 PNG 头部与像素特征——长宽整数倍（如 `1024×256` 4 帧横排）自动投票 `vfx/anim` 序列帧；正方形带 Alpha（`256×256` / `512×512`）投票 UI/图标；竖幅带 Alpha（`512×1024`）识别全身立绘；`16:9` 无 Alpha 大图识别场景气氛图。
4. **现有模块与父子继承匹配（权重 0.15）**：同一个角色生成了不同画风（如 `character.Astra` 已有正比立绘，新生成 Q 版或水彩），自动分叉为子模块 `character.Astra.Chibi` / `character.Astra.Watercolor` 并设置 `parent: character.Astra`，同时按画风智能适配管线规格（如水彩概念图不强制要求透明底）。
5. **低置信度兜底保护**：无 Prompt 且特征模糊的图片（置信度 `< 0.55`）归入 `misc.<Entity>` 且状态保持 `candidate`，绝不静默污染正式生产模块。

---

## 🏗️ 核心架构与目录一览

### 5+1+1 美术领域分类树（Taxonomy）

| 领域前缀 | 名称 | 典型管理对象 | 默认关键管线规格 |
| :--- | :--- | :--- | :--- |
| **`brand.*`** | 全局风格圣经 | 世界观色彩脚本、70/20/10 配比、全局禁用词 | `sRGB`、`16:9` 色卡基准 |
| **`character.*`** | 角色与立绘差分 | 立绘、三视图、表情差分、多画风子模块（`.Chibi` / `.Watercolor`） | 立绘要求 `RGBA` 透明底 + 16px 安全留白；概念画风分叉可放宽 Alpha |
| **`scene.*`** | 场景与物件 | 气氛概念图、等轴测建筑、Tilemap 地块、光影基准 | `16:9` 构图、主光源角度一致性 |
| **`ui.*`** | 界面与九宫格 | 弹窗底框、HUD 图标、按钮状态、字体层级 | `RGBA`、`nine_slice: [48,48,48,48]`、中心拉伸区禁放具象花纹 |
| **`vfx.*`** | 特效与序列帧 | 刀光受击序列帧、粒子贴图、Shader 溶解噪声 | 整除帧网格、Premultiplied Alpha、禁止黑底实心导出 |
| **`anim.*`** | 骨骼与序列动画 | Spine / Live2D 拆件图层、动作帧循环规范 | 图层命名契约、旋转轴心与闭合补画要求 |
| **`misc.*`** | 待归类候选池 | 低置信度或未知类型的临时生成物 | 状态固定为 `candidate`，待人工确认后晋升 |

### 7 种结构化美术记忆类型（Memory Kinds）

| 记忆类型 (`kind`) | 用途 | 生命周期 |
| :--- | :--- | :--- |
| **`style_redline`** | **主美审美红线（Do vs. Don't）**：记录曾被打回的废案原因与正反例对比图 | 常驻强约束 |
| **`pipeline_constraint`** | **工程管线硬规格**：分辨率、Alpha 通道、九宫格切线、边缘安全像素、色彩空间 | 常驻强约束 |
| **`visual_correction`** | **审稿打回修正记录**：记录某次具体局部崩坏（如手指、透视、图层命名）的返修前后对比 | 常驻经验 |
| **`art_decision`** | **世界观与方向拍板**：定调色板 HEX 配比、镜头角度、材质表现取舍 | 常驻定调 |
| **`recipe`** | **AI 生图标准配方**：经过验证可复现的底模、LoRA 权重、Seed、正负向 Prompt 与 ComfyUI 工作流 | 常驻可复现 |
| **`asset_record`** | **定稿资产入库台账**：记录通过验收的最终图路径、SHA-256 指纹与用途（`ingest` 自动生成桩） | 资产台账 |
| **`art_plan`** | **待补齐资产清单**：某模块尚未绘制或待优化的差分、帧数或拆件任务 | 完成后归档 |

### 仓库文件结构

```text
pmem-art/
├── art-atlas.html                 # 🌟 单文件自包含可视化美术记忆图谱工作台（双击即用）
├── pmem_art.py                    # 🐍 主 CLI 入口（init/bootstrap/sync/classify/ingest/search/validate/doctor/atlas）
├── classify.py                    # 🧭 四信号融合分类器 + 自动扩模块 + 资产入库引擎
├── lifecycle.py                   # 🔄 Mode A/B/C 生命周期、候选池管理、零依赖 YAML 读写器
├── build_atlas.py                 # 🏗️ art-atlas.html 静态图谱编译器（内嵌缩略图与交互工作台）
├── README.md                      # 📖 项目主页说明
├── USER_MANUAL.md                 # 📘 完整分步使用手册（七章全指令与配置详解）
├── ARCHITECTURE.md                # 🧠 架构设计白皮书
├── LICENSE                        # ⚖️ GNU GPL v3.0 开源许可证
├── .memory-art/                   # 🗄️ 随 Git 提交的美术记忆库（Project-Celadon 完整示例数据）
│   ├── config.yaml                #   - 项目级色彩空间、生命周期模式、闸门与分类器权重配置
│   ├── modules.yaml               #   - 美术模块树、色板 HEX、分辨率/Alpha/九宫格契约
│   ├── candidates.json            #   - 待确认候选模块队列
│   ├── entries/<module>/<id>.md   #   - 7 大类美术记忆条目（YAML Frontmatter + Markdown + 视觉锚点）
│   └── specs/<module>/*.md        #   - 模块四维规范文档（视觉设定 / 管线规格 / AI生成配方 / 资产台账）
├── assets/                        # 🎨 示例美术资产（含内嵌 PNG tEXt 元数据的正反例图片）
├── workflows/                     # ⚙️ ComfyUI 标准生图工作流 JSON 锚点
└── .cursor/                       # 🤖 Cursor Rules (`.mdc`)、双端闸门 (`hooks.json`) 与 MCP 配置
```

---

## 🛠️ CLI 全指令速查表

| 指令 | 示例 | 说明 |
| :--- | :--- | :--- |
| **`init`** | `python3 pmem_art.py init --name "MyProject"` | 冷启动初始化 `.memory-art/`、6 大领域空目录与 Cursor 规则 |
| **`bootstrap`** | `python3 pmem_art.py bootstrap --mode young --apply` | `young` 确认脚手架；`legacy` 扫描存量乱资产并生成候选与报告 |
| **`sync`** | `python3 pmem_art.py sync` | 扫描资产目录新增文件夹，更新候选模块队列 |
| **`candidates`** | `python3 pmem_art.py candidates` | 列出当前待确认的候选模块、文件数与置信度 |
| **`accept`** | `python3 pmem_art.py accept character.Astra` 或 `--all` | 将候选模块提升为 `active`（`--all` 仅提升候选，不误升空脚手架） |
| **`classify`** | `python3 pmem_art.py classify a.png -p "角色Astra 立绘"` | 多信号分类预测（输出建议模块、置信度、画风分叉、图像特征 JSON） |
| **`ingest`** | `python3 pmem_art.py ingest a.png -p "..." --apply` | 分类 → 自动扩充 `modules.yaml` → 归位文件 → 生成 `asset_record` 记忆桩 |
| **`classify-watch`** | `python3 pmem_art.py classify-watch --apply` | 扫描 `watch_dirs`（如 `.cursor/generated`）中未映射的新图并批量分类/入库 |
| **`place`** | `python3 pmem_art.py place --plan-orphans [--apply]` | 规划或执行孤儿资产归位（默认 dry-run 预览，加 `--apply` 才移动磁盘文件） |
| **`list`** | `python3 pmem_art.py list` | 列出全部模块、记忆数、图片数、红线数与健康状态 |
| **`search`** | `python3 pmem_art.py search --module ui.InventoryHUD` | 召回指定模块或路径的完整记忆上下文（含父模块继承与全局色彩圣经） |
| **`validate`** | `python3 pmem_art.py validate` | 逐图检验分辨率、RGBA 透明通道、边缘安全留白与 SHA-256 Stale 状态 |
| **`doctor`** | `python3 pmem_art.py doctor` | 全项目体检：模块覆盖率 %、孤儿文件清单、多风格冲突提示 + 资产质检 |
| **`atlas`** | `python3 pmem_art.py atlas` | 将最新资产与记忆重新编译为单文件交互式 `art-atlas.html` |
| **`hook`** | `python3 pmem_art.py hook pre-gen \| post-asset \| stop` | 供 Cursor / Claude Code 调用的自动化生图前召回与落盘后质检闸门 |

---

## 📚 深入阅读

- 📘 **[完整使用手册 (`USER_MANUAL.md`)](./USER_MANUAL.md)**：从零安装、三种项目接入实操、模块与多画风拆分规范、7 种记忆编写模板、`art-atlas.html` 界面详解到 Cursor Hook 配置的完整教程。
- 🧠 **[架构设计文档 (`ARCHITECTURE.md`)](./ARCHITECTURE.md)**：设计哲学、四信号分类数学模型、生命周期状态机与像素级质检实现细节。

---

## ⚖️ 开源许可证 (License)

本项目基于 **[GNU General Public License v3.0 (GPL-3.0)](./LICENSE)** 开源发布，与 [`mry-ship/pmem`](https://github.com/mry-ship/pmem) 保持一致。
