# 📘 `pmem-art` 完整使用手册 (User Manual v0.7.0)

> **适用版本**：`v0.7.0`  
> **运行环境**：Python `>= 3.10`（纯标准库实现，零第三方依赖，跨 macOS / Linux / Windows 开箱即用）  
> **配合工具**：Cursor / Claude Code / Codex / ComfyUI / Stable Diffusion WebUI / Spine / Aseprite

---

## 目录

1. [第一章：快速上手与目录结构说明](#第一章快速上手与目录结构说明)
2. [第二章：三种项目接入指南（Mode A / B / C 完整实操）](#第二章三种项目接入指南mode-a--b--c-完整实操)
3. [第三章：美术模块划分与多画风 / 动画隔离规范](#第三章美术模块划分与多画风--动画隔离规范)
4. [第四章：七种美术记忆类型编写指南与模板](#第四章七种美术记忆类型编写指南与模板)
5. [第五章：可视化美术图谱工作台 `art-atlas.html` 操作指南](#第五章可视化美术图谱工作台-art-atlashtml-操作指南)
6. [第六章：命令行全指令参考手册](#第六章命令行全指令参考手册)
7. [第七章：Cursor / Claude Code 自动闸门配置与常见问题排查（FAQ）](#第七章cursor--claude-code-自动闸门配置与常见问题排查faq)

---

## 第一章：快速上手与目录结构说明

### 1.1 为什么零依赖？
美术与游戏工程团队的机器环境差异极大（策划、主美、原画师未必装了复杂的 Python 虚拟环境或 C 扩展库）。因此 `pmem-art` 的核心解析器（包含 PNG `IHDR` 头读取、四角与边缘 Alpha 像素采样、SHA-256 指纹校验、YAML 子集读写、HTML 图谱编译）**100% 使用 Python 标准库编写**。只要机器上有 `python3`（3.10+），即可直接运行。

### 1.2 核心目录与文件职责

将 `pmem-art` 放入你的项目根目录（或通过 `--root /path/to/project` 指定目标项目路径）后，核心结构如下：

```text
your-project/
├── pmem_art.py                    # 主命令行入口
├── classify.py                    # 多信号分类器与自动入库引擎
├── lifecycle.py                   # 生命周期（init/bootstrap/sync/accept/place）引擎
├── build_atlas.py                 # 静态单文件图谱编译器
├── art-atlas.html                 # 编译产出的可视化美术图谱（可直接双击在浏览器打开）
├── .memory-art/                   # 【核心】随 Git 提交的美术记忆中心
│   ├── config.yaml                # 全局配置（色彩空间、生命周期策略、分类阈值、Hook 开关）
│   ├── modules.yaml               # 模块注册表（path_globs、status、specs、palette）
│   ├── candidates.json            # 扫描发现但尚未转正的候选模块队列
│   ├── entries/                   # 按模块存放的 Markdown 记忆卡
│   │   ├── brand.GlobalStyle/
│   │   ├── character.Astra/
│   │   └── ...
│   └── specs/                     # 按模块存放的四维基础规范文档
│       └── <module_id>/
│           ├── 01-视觉设定.md
│           ├── 02-管线规格.md
│           ├── 03-AI生成配方.md
│           └── 04-资产台账.md
└── .cursor/
    ├── rules/pmem-art.mdc         # Cursor Agent 自动遵循的生图前/落盘后规则
    └── hooks.json                 # 自动触发钩子配置
```

---

## 第二章：三种项目接入指南（Mode A / B / C 完整实操）

不同的项目处于不同的生命周期阶段。`pmem-art` 提供了三套互不冲突的接入路径：

---

### 2.1 模式 A：空项目 / 刚立项冷启动（Young / Empty Project）

**场景**：项目刚建仓，还没有美术图，或者只有零星一两张概念图。希望一开始就建立清晰的目录规范，并在后续使用 Cursor 生图时自动按模块归档。

#### 操作步骤：
```bash
# 步骤 1：在目标项目根目录初始化 .memory-art 与 6 大基础资产目录
python3 pmem_art.py --root /path/to/my-game init --name "MyGame"

# 步骤 2：以年轻项目模式（young）启动，开启自动归位
python3 pmem_art.py --root /path/to/my-game bootstrap --mode young --apply
```

#### 执行效果：
1. 自动创建 `assets/brand/`、`assets/character/`、`assets/scene/`、`assets/ui/`、`assets/vfx/`、`assets/anim/` 六个标准空目录。
2. 在 `.memory-art/modules.yaml` 中生成 `brand.GlobalStyle`（`active` 状态）以及 `character.Starter`、`scene.Starter`、`ui.Starter`、`vfx.Starter`、`anim.Starter` 五个脚手架模块（`scaffold` 状态）。
3. 在 `.memory-art/config.yaml` 中设置 `bootstrap.mode: young` 和 `bootstrap.auto_place: true`。

---

### 2.2 模式 B：已有大量历史乱资产的老项目接入（Legacy Project）

**场景**：项目已经开发了几个月甚至一年，图片散落在 `Art/Characters/Hero/`、`Content/UI_Old/`、`res/fx/` 等五花八门的目录中。
**铁律**：**老项目严禁任何工具未经允许自动搬移磁盘文件**（一旦改路径，Unity `.meta` / Unreal 引用 / 引擎配置全部断裂）。

#### 操作步骤：
```bash
# 步骤 1：只读扫描存量目录，按目录深度与关键词自动聚类出候选模块（绝不移动文件！）
python3 pmem_art.py --root /path/to/legacy-game bootstrap --mode legacy --roots Art Content assets

# 步骤 2：查看扫描生成的诊断报告与候选模块列表
cat /path/to/legacy-game/.memory-art/LEGACY_BOOTSTRAP_REPORT.md
python3 pmem_art.py --root /path/to/legacy-game candidates

# 步骤 3：将认可的候选模块提升为正式 active 模块
# 可以单个接受：
python3 pmem_art.py --root /path/to/legacy-game accept character.Astra
# 也可以一键接受所有扫描出的候选模块（不会误升空的 Starter 脚手架）：
python3 pmem_art.py --root /path/to/legacy-game accept --all

# 步骤 4：运行全量体检，查看模块覆盖率、孤儿文件与多风格混放告警
python3 pmem_art.py --root /path/to/legacy-game doctor
```

#### 如果老项目里有散落在根目录的「孤儿图」想归位怎么办？
```bash
# 先预览移动计划（Dry-Run，只打印不移动）
python3 pmem_art.py --root /path/to/legacy-game place --plan-orphans

# 人工确认目标路径无误后，显式加 --apply 执行归位
python3 pmem_art.py --root /path/to/legacy-game place --plan-orphans --apply
```

---

### 2.3 模式 C：在 Cursor 中持续生图与多信号自动扩模块（Continuous AI Generation）

**场景**：你在 Cursor 里通过 `GenerateImage`、MCP 生图插件或本地 ComfyUI 不断产出新图片（例如存放在 `.cursor/generated/` 或 `inbox/`），希望根据生图时的 Prompt、文件名和图片本身特征，自动判断它属于哪个角色/场景/UI/特效、属于什么画风，并自动在 `modules.yaml` 里创建或扩展模块、移动归位、写好记忆台账。

#### 操作步骤：

**① 单张新图分类预览（不改文件，仅看四信号推理结果）**
```bash
python3 pmem_art.py classify .cursor/generated/cursor_01_astra_stand.png \
  --prompt "角色Astra 主角立绘 青瓷白与深海墨蓝长袍 透明背景 全身"
```
输出的 JSON 会清晰展示：
- `category`: `"character"`
- `entity`: `"Astra"`
- `suggested_module`: `"character.Astra"`
- `confidence`: `0.85`
- `signals`: 拆解列出 `prompt`、`path`、`image_traits`（如检测到 `512x1024` 竖幅 + `RGBA` 透明底）、`existing_module` 四项各自得多少分。

**② 单张新图一键入库（自动扩模块 + 移动文件 + 生成 `asset_record` 记忆桩）**
```bash
python3 pmem_art.py ingest .cursor/generated/cursor_01_astra_stand.png \
  --prompt "角色Astra 主角立绘 青瓷白与深海墨蓝长袍 透明背景 全身" \
  --apply
```
执行后：
1. 若 `character.Astra` 尚不存在，自动在 `modules.yaml` 中增量写入 `character.Astra`（设置 `path_globs: ["assets/character/Astra/**"]` 及角色立绘默认 `RGBA` 管线规格），并初始化 `.memory-art/specs/character.Astra/` 下的四份规范文档。
2. 将图片移动到 `assets/character/Astra/cursor_01_astra_stand.png`。
3. 在 `.memory-art/entries/character.Astra/` 下自动生成一条带 SHA-256 指纹与 Prompt 记录的 `asset_record` 记忆卡。

**③ 同角色不同画风自动分叉（Style Fork）**
当你接着为同一个角色生成一张水彩概念图或 Q 版贴纸时：
```bash
python3 pmem_art.py ingest .cursor/generated/cursor_02_astra_watercolor.png \
  --prompt "角色Astra 水彩画风 概念图 半身柔和光影" \
  --apply
```
分类器识别到实体仍是 `Astra`，但带有显式画风信号 `Watercolor (水彩)`：
- **绝不与正比立绘混放**！自动创建子模块 **`character.Astra.Watercolor`**，并自动设置 `parent: character.Astra`。
- 自动将图片归入隔离目录 `assets/character/Astra/Watercolor/`。
- **智能管线适配**：水彩/概念图子模块自动将 `alpha_required` 设为 `false`，避免后续 `doctor` 体检误报「概念图缺少透明通道」。

**④ 批量扫描监听目录（`classify-watch`）**
如果一次生成了多张图放在 `.cursor/generated/`：
```bash
# 预览所有未归档新图的分类结果
python3 pmem_art.py classify-watch

# 批量执行入库与扩模块
python3 pmem_art.py classify-watch --apply
```
> **安全兜底**：对于既没有传 Prompt、文件名又叫 `mystery_blob_99.png` 的低置信度图片（`< 0.55`），`ingest` 会将其放入 `misc.<Entity>` 且模块状态保持为 **`candidate`（候选）**，并在 `doctor` 中提示人工复核，绝不污染正式生产模块。

---

## 第三章：美术模块划分与多画风 / 动画隔离规范

### 3.1 `modules.yaml` 结构详解

每个美术模块在 `.memory-art/modules.yaml` 中定义如下：

```yaml
  - id: character.Astra
    name: "主角·阿斯特拉 (Astra) 立绘与差分"
    category: character
    status: active
    parent: brand.GlobalStyle
    description: "女主阿斯特拉的标准立绘、面部表情差分与服装配件设定"
    owner: "Lead Character Artist"
    path_globs:
      - "assets/character/Astra/*"
    specs:
      resolution_ standard: "512x512 (预览基准) / 2048x2048 (源图)"
      aspect_ratio: "1:1"
      color_space: "sRGB"
      alpha_required: true
      safe_margin_px: 16
      head_to_body_ratio: "7.5头身（严禁Q版化或低于6.5头身）"
    palette:
      - name: "袍服主色·青瓷白"
        hex: "#D8E6E7"
      - name: "披风底色·深海墨蓝"
        hex: "#132238"
      - name: "星盘饰品·流光金"
        hex: "#E5B869"
```

### 3.2 父子模块继承机制（`parent`）
当你查询子模块（例如 `python3 pmem_art.py search --module character.Astra.Chibi`）时，系统会沿着 `parent` 链条自动向上聚合：
1. **`brand.GlobalStyle`**：全局世界观色彩圣经与通用红线
2. **`character.Astra`**：角色本体的核心特征（发色、瞳色、标志性星盘配饰）
3. **`character.Astra.Chibi`**：当前子模块特有的头身比（2.5 头身）与贴纸描边规范

### 3.3 同一角色多画风隔离规范
切勿将同一角色的正比立绘、Q版表情包、水彩插画混在同一个无子目录的 glob 下（否则 `doctor` 会触发多画风冲突告警，且管线质检无法同时满足透明底与非透明底要求）。推荐拆分方式：
- 正比立绘本体：`character.Astra` → `assets/character/Astra/*.png`（不含子文件夹通配 `**`，或明确排除子目录）
- Q版画风分支：`character.Astra.Chibi`（`parent: character.Astra`）→ `assets/character/Astra/Chibi/**`
- 水彩概念分支：`character.Astra.Watercolor`（`parent: character.Astra`）→ `assets/character/Astra/Watercolor/**`

### 3.4 动画与特效模块隔离规范（`anim.*` vs `vfx.*`）
- **`anim.<Entity>`**：用于管理 Spine / Live2D 骨骼拆件图层、角色待机/奔跑/攻击动作循环帧。重点约束图层闭合补画、旋转轴心（Pivot）与命名契约。
- **`vfx.<EffectName>`**：用于管理刀光、受击火花、法阵序列帧与 Shader 噪声贴图。重点约束序列帧网格整除（如 `4x1` 横排）、Premultiplied Alpha（预乘透明）与禁黑底导出。

---

## 第四章：七种美术记忆类型编写指南与模板

所有记忆文件均保存在 `.memory-art/entries/<module_id>/<MEMORY_ID>.md`，采用 **YAML Frontmatter + Markdown 正文** 格式，可直接纳入 Git 版本控制与 Code Review。

### 4.1 主美审美红线 (`style_redline`) —— 最核心的防翻车武器
用于记录明确禁止的画风偏移、色彩污染或比例崩坏，强烈建议同时挂载 `reference_do`（正确基准图）与 `reference_dont`（被打回废案图）：

```markdown
---
id: ART-CHAR-001
title: "阿斯特拉立绘红线：严禁赛博荧光紫溢色与Q版5头身比例崩坏"
kind: style_redline
module: character.Astra
severity: blocker
status: active
created_at: "2026-10-12"
updated_at: "2026-10-24"
tags: ["立绘红线", "头身比", "禁止霓虹紫", "正反例对比"]
reference_do: "assets/character/Astra/astra_portrait_do.png"
reference_dont: "assets/character/Astra/astra_portrait_dont_neon.png"
anchor_hashes:
  "assets/character/Astra/astra_portrait_do.png": "87639a2b86934bc817a0e403269395d845834b86a931efbd167b148aa78f2592"
---

## 为什么立这条红线（打回原因）
AI 生图或外包画师在未加载色板约束时，极易把「东方青瓷幻境」误画成「赛博朋克霓虹紫（`#FF00FF`）」，且默认人像权重常把 7.5 头身压缩成 5 头身萌系比例。

## 强制执行标准（Do vs. Don't）
- ✅ **DO（正确示范）**：保持 7.5 头身修长比例；受光面严格使用青瓷白 `#D8E6E7` 与流光金 `#E5B869`。
- ❌ **DON'T（一票否决）**：严禁出现品红/紫红环境光；严禁大头短腿 Q 版化；严禁不透明黑底导出。
```

### 4.2 工程管线硬规格 (`pipeline_constraint`)
记录进引擎前必须满足的客观技术指标（如 UI 九宫格切线、边距、Alpha 通道）：

```markdown
---
id: ART-UI-001
title: "UI九宫格弹窗硬性规范：48px切线圆角保护与中心区禁画具象圆环"
kind: pipeline_constraint
module: ui.InventoryHUD
severity: blocker
status: active
created_at: "2026-10-14"
updated_at: "2026-10-24"
tags: ["九宫格", "9-slice", "UI拉伸", "圆角保护"]
reference_do: "assets/ui/InventoryHUD/panel_frame_9slice_do.png"
reference_dont: "assets/ui/InventoryHUD/panel_frame_9slice_dont.png"
---

## 管线技术参数
- **九宫格切线 (`nine_slice`)**：左 `48px` / 右 `48px` / 上 `48px` / 下 `48px`
- **拉伸规则**：四角 `48x48` 区域存放青铜云纹转角（完全不拉伸）；中央区域会被引擎任意宽高比拉伸，**严禁在中心区域绘制圆形阵法或具象图案**。
```

### 4.3 AI 生图标准配方 (`recipe`)
沉淀经过验证可稳定复现的 Checkpoint、LoRA、Seed 与正负向提示词：

```markdown
---
id: ART-CHAR-002
title: "阿斯特拉标准半身立绘 ComfyUI 可复现生图配方 (Seed 20261024)"
kind: recipe
module: character.Astra
severity: high
status: active
created_at: "2026-10-15"
updated_at: "2026-10-24"
tags: ["ComfyUI", "LoRA配方", "可复现Seed", "立绘生成"]
reference_do: "assets/character/Astra/astra_portrait_do.png"
recipe:
  engine: "ComfyUI"
  workflow_file: "workflows/comfyui_celadon_char_v2.json"
  checkpoint: "celadon_oriental_fantasy_v24.safetensors"
  loras:
    - name: "celadon_glaze_lineart_v3.safetensors"
      strength_model: 0.75
    - name: "astra_char_sheet_v1.safetensors"
      strength_model: 0.85
  sampler: "dpmpp_2m_sde_gpu"
  scheduler: "karras"
  steps: 32
  cfg: 6.5
  seed: 20261024
  resolution: "512x512"
  positive_prompt: "masterpiece, best quality, 1girl, astra, celadon white robe (#D8E6E7), deep ink blue cape (#132238), golden astrolabe ornament (#E5B869), 7.5 heads tall proportion, clean transparent background, soft rim light"
  negative_prompt: "cyberpunk, neon purple, magenta light, chibi, 5 heads tall, deformed hands, extra fingers, solid black background, jpeg artifacts"
---
```

### 4.4 其余四种记忆类型速览
- **`visual_correction`（审稿打回修正记录）**：记录某次具体返修（例如「手握星盘透视穿模修正」「Spine 呼吸动作胸腔断层补画」）。
- **`art_decision`（世界观与视觉方向拍板）**：记录主美与制作人拍板的定调决策（如「全局采用 70% 低饱和青灰 + 20% 墨蓝 + 10% 流光金配比」）。
- **`asset_record`（定稿资产入库台账）**：记录已验收资产的文件路径、尺寸、SHA-256 指纹与生图来源（执行 `ingest --apply` 时会自动生成）。
- **`art_plan`（待补齐资产清单）**：记录某模块还缺哪些表情差分、动作帧或图标状态。

---

## 第五章：可视化美术图谱工作台 `art-atlas.html` 操作指南

每次新增或修改了美术资产与记忆后，只需运行：

```bash
python3 pmem_art.py atlas
```

即可在项目根目录重新生成单文件自包含的 **`art-atlas.html`**。直接用浏览器打开它，你将拥有五大专业视图：

### 5.1 🖼️ 画廊瀑布流与视觉锚点 (Gallery & Moodboard)
- **模块筛选栏**：左侧按 `brand` / `character` / `scene` / `ui` / `vfx` / `anim` 分组切换，顶部实时展示当前模块的**定调色板色卡（点击色卡可直接复制 `#HEX` 色值）**与管线硬规格芯片。
- **四种查图画布底色实时切换**（右上角工具栏）：
  1. **🏁 棋盘格透明底**：检验 Alpha 通道是否正确抠除。
  2. **🌑 深灰暗房底 (`#18181b`)**：检验边缘是否有残留亮白杂边（Halo）。
  3. **📜 宣纸亮白底 (`#f5f2eb`)**：检验暗部轮廓与浅色半透明特效在亮底下的辨识度。
  4. **🌌 实机夜色环境底 (`#0c1824`)**：模拟游戏实机夜晚场景下的融合度。
- **九宫格切线叠加开关 (`📐 9-Slice`)**：开启后，所有定义了 `nine_slice` 的 UI 资产卡片上会自动叠加青色虚线切线框，直观检验圆角保护区是否被侵入。
- **缩略图无极缩放滑杆**：从 `160px` 紧凑网格到 `420px` 高清大图自由拖动。

### 5.2 🚫 正反例红线滑杆对比台 (Do vs. Don't Redlines)
- 将每一条配有正反例图片的 `style_redline` / `pipeline_constraint` 渲染为**交互式左右分割滑杆（Before / After Split Slider）**。
- 左右拖动中间的分隔手柄，即可在同一像素位置对比 **✅ DO 定稿基准图** 与 **❌ DON'T 翻车废案图**，彻底消除文字描述的歧义。

### 5.3 🧪 AI 生图配方工作台 (AI Recipes & Prompt Copy)
- 集中展示所有 `recipe` 记忆卡中的底模、LoRA 权重表、采样器、Seed 以及完整正负向 Prompt。
- 提供 **「复制 Positive Prompt」**、**「复制 Negative Prompt」** 与 **「复制完整 Agent 上下文」** 一键按钮，贴入 ComfyUI 或 Cursor 对话框即可复现。

### 5.4 📐 模块四维规范与 🩺 管线质检台 (Specs & Stale Doctor)
- 在线审阅每个模块的《01-视觉设定》《02-管线规格》《03-AI生成配方》《04-资产台账》。
- 实时列出每个文件的分辨率、色彩模式（`RGBA` / `RGB`）、SHA-256 指纹校验结果与 PNG 内嵌 `tEXt` 元数据，任何被外部偷改而未更新记忆的资产都会高亮标记为 `STALE`。

---

## 第六章：命令行全指令参考手册

所有命令均支持全局参数 `--root <项目路径>`（默认当前目录 `.`）。

### 6.1 项目生命周期与模块管理

| 命令与参数 | 作用详解 |
| :--- | :--- |
| `python3 pmem_art.py init [--name <项目名>]` | 初始化 `.memory-art/` 目录结构、6 大领域空资产文件夹、`brand.GlobalStyle` 与 5 个 `scaffold` 脚手架模块，以及 `.cursor/rules/pmem-art.mdc`。 |
| `python3 pmem_art.py bootstrap --mode young [--apply]` | 年轻项目冷启动确认，开启 `auto_place: true`，后续 `ingest` 自动扩模块并归位文件。 |
| `python3 pmem_art.py bootstrap --mode legacy [--roots Dir1 Dir2]` | 存量老项目无损接入：扫描指定目录树，按文件夹层级与关键词聚类生成 `candidate` 模块与 `LEGACY_BOOTSTRAP_REPORT.md`，**绝不移动任何现有文件**。 |
| `python3 pmem_art.py sync` | 日常增量同步：扫描资产目录，将新出现的未映射子目录加入候选模块队列。 |
| `python3 pmem_art.py candidates` | 查看当前 `candidates.json` 中待确认的候选模块、文件数、推断领域与置信度。 |
| `python3 pmem_art.py accept <module_id> \| --all` | 将指定候选模块（或全部候选模块）状态提升为 `active`，并自动补齐其 `specs/` 四维规范文档。 |

### 6.2 多信号分类与自动入库（Cursor 持续生图核心）

| 命令与参数 | 作用详解 |
| :--- | :--- |
| `python3 pmem_art.py classify <img_path> [-p "<Prompt>"]` | **只读分类预测**：综合 Prompt、路径词、PNG 物理特征（尺寸/长宽比/Alpha/序列帧网格）与现有模块树，输出 JSON 格式的分类报告（含建議模块、画风分叉、置信度与四维信号得分明细）。 |
| `python3 pmem_art.py ingest <img_path> [-p "<Prompt>"] [--apply]` | **分类 + 扩模块 + 归位 + 记台账**：不加 `--apply` 时为预览模式；加 `--apply` 后自动在 `modules.yaml` 注册新模块（或画风子模块）、将图片移入目标模块目录，并生成 `asset_record` 记忆卡。 |
| `python3 pmem_art.py classify-watch [--apply]` | 批量扫描 `config.yaml` 中配置的 `watch_dirs`（如 `.cursor/generated`、`assets`）下所有未映射图片，批量执行分类与入库。 |
| `python3 pmem_art.py place [--plan-orphans] [--apply]` | 为散落在模块外的孤儿图片生成归位移动计划；加 `--apply` 后执行文件移动。 |

### 6.3 记忆检索、管线质检与图谱编译

| 命令与参数 | 作用详解 |
| :--- | :--- |
| `python3 pmem_art.py list` | 打印所有已注册模块的汇总表（状态、记忆条目数、关联图片数、红线数、质检状态）。 |
| `python3 pmem_art.py search [-m <module>] [-p <file_path>] [-k <kind>] [-q <keyword>] [--json]` | 按模块 ID、文件路径、记忆类型或关键词检索美术记忆。指定 `-m` 时会自动向上继承父模块与 `brand.GlobalStyle` 的全部红线与色板。 |
| `python3 pmem_art.py validate` | 逐一校验所有模块下的图片是否符合 `specs`（检查 `RGBA` 透明通道、四边安全留白像素、SHA-256 锚点是否过期）。若有违规返回非零退出码。 |
| `python3 pmem_art.py doctor` | 全项目深度体检：计算**资产模块覆盖率 %**、列出未归管孤儿图片、检测同一模块下多画风混放冲突，并汇总全部管线质检结果。 |
| `python3 pmem_art.py atlas` | 重新扫描全项目模块、记忆与图片，编译生成最新的单文件交互式工作台 `art-atlas.html`。 |
| `python3 pmem_art.py hook <pre-gen \| post-asset \| stop>` | 供 AI Agent 自动调用的生命周期钩子（生图前强注入红线与色板；落盘后自动触发像素质检）。 |

---

## 第七章：Cursor / Claude Code 自动闸门配置与常见问题排查（FAQ）

### 7.1 Cursor Rules 自动生效机制
在项目根目录包含 `.cursor/rules/pmem-art.mdc` 后，Cursor Agent 在处理任何美术生图、改图、切图或整理资产任务时会自动遵守三大闸门：
1. **生图前闸门（Pre-Generation Gate）**：调用生图工具前，先运行 `python3 pmem_art.py search --module <目标模块>` 读取主美红线（`style_redline`）、色板 HEX 与标准配方（`recipe`），将其中的禁用词自动并入 Negative Prompt。
2. **持续生图归档闸门（Continuous Ingest Gate）**：新生成的图片落盘后，运行 `python3 pmem_art.py ingest <新图路径> --prompt "<生图指令>" --apply` 完成自动分类、子模块扩展与台账登记。
3. **落盘后质检闸门（Post-Asset Gate）**：交付给用户前运行 `python3 pmem_art.py doctor` 与 `python3 pmem_art.py atlas`，确保无透明底缺失、无尺寸违规且可视化图谱保持最新。

### 7.2 常见问题排查（FAQ）

#### Q1：为什么水彩概念图或场景气氛图没有透明背景（是 `RGB` 而非 `RGBA`），`doctor` 却没有报错？
**答**：因为 `pmem-art` 的分类器与模块规格支持**按领域与画风差异化质检**。`scene.*`（场景）、`brand.*`（色卡）以及带有 `Watercolor`（水彩）/ `Concept`（概念图）画风分叉的模块会自动将 `alpha_required` 设为 `false`；只有正比立绘（`character.*` 主模块）、UI 切图（`ui.*`）、特效（`vfx.*`）与骨骼拆件（`anim.*`）才强制要求 `RGBA` 透明通道。

#### Q2：我不小心用 Photoshop / Aseprite 直接修改了某张定稿基准图，`doctor` 报 `[STALE] SHA-256 哈希与记忆锚点不一致` 怎么办？
**答**：这正是 `pmem-art` 的**视觉防漂移锚点机制**在生效！提醒你「图片像素已经变了，请确认对应的记忆文档或生图配方是否需要同步更新」。确认新图无误后，将记忆 Markdown 文件 `anchor_hashes` 中的哈希值更新为报错信息里提示的新 SHA-256 值，再运行 `python3 pmem_art.py atlas` 即可恢复 `PASS`。

#### Q3：如果一张图片完全没有 Prompt，文件名也是乱码（如 `img_0099.png`），`ingest` 会把它乱塞进某个角色模块吗？
**答**：**绝不会**。当四信号综合置信度低于阈值（默认 `0.55`）时，分类器会将其归入 `misc.<Entity>` 兜底分类，且模块状态设为 `candidate`（待确认候选），不会污染任何 `active` 生产模块。你可以稍后通过 `candidates` 查看并人工移动到正确模块。
