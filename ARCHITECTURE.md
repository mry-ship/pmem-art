# 🧠 `pmem-art` 深度架构设计文档：从代码记忆（`pmem`）到视觉与 AI 美术记忆

## 一、为什么要专门为美术与 AI 美术做 `pmem-art`？

原版 `mry-ship/pmem` 解决了软件工程中 AI 改代码“记不住历史踩坑、不查模块契约”的问题。但在**游戏与数字内容美术生产（人类画师 + 主美审稿 + AI 美术 Agent）**中，痛点截然不同：

1. **视觉风格极易跑偏（Style Drift）**：AI 美术（ComfyUI / Flux / SD / Midjourney）每次生成新立绘、新图标或表情差分时，如果没有读取该模块的**主色板（Palette HEX）**、**头身比/透视约束**和**主美曾打回的废案红线（Do vs. Don't）**，极易生成出“好看但完全不像同一个游戏”的废图。
2. **引擎管线硬指标翻车（Pipeline Violations）**：
   - 要求导出 **RGBA 透明背景 + 预乘 Alpha**，AI 却生成了实心白底或灰黑底，进引擎做 Additive/Blend 混合时整块发白；
   - UI 弹窗要求 **九宫格（9-slice `[48, 48, 48, 48]`）中心拉伸区纯净**，AI 却在正中央画了圆形大徽章和斜向纹理，程序一拉伸直接畸变；
   - 角色需要拆 **Spine 2D 骨骼图层**（前发/后发/瞳孔/高光独立），或者特效需要 **4 帧等宽横排序列帧**，缺乏明确记忆约束就会反复返工。
3. **配方与随机种子丢失（Lost Recipes）**：某张过稿图效果极佳，但几天后要做同系列换装或差分时，当时的 **Base Model、LoRA 权重配比、Prompt 模板、Negative 词库、ControlNet 预处理器和 ComfyUI 工作流 JSON** 散落在个人聊天记录里，无法稳定复现。
4. **人类美术查资料习惯是“视觉优先”而非“读纯文本”**：程序员习惯看 Markdown 列表，而美术师与主美需要**在一个页面里直接铺开小模块的所有图片（Moodboard / 缩略图墙）**，切换棋盘格底色查边缘、拉动滑杆对比正反例、点击吸取标准色卡。

---

## 二、`pmem` vs `pmem-art` 核心维度深化对比

| 维度 | 代码版 `mry-ship/pmem` | 美术深化版 `pmem-art` |
| :--- | :--- | :--- |
| **模块划分 (`modules.yaml`)** | 按代码目录与服务划分（如 `auth`, `payment`, `api`） | 按 **5 大美术生产域 + 父子继承树** 划分：`brand.*`（色彩圣经）、`character.*`（立绘/三视图/子模块 `Expressions` 差分）、`scene.*`（等轴测地块/光照）、`ui.*`（HUD/九宫格/图标）、`vfx.*`（刀光序列帧/粒子） |
| **模块元数据契约** | `paths` 代码路径映射、`synonyms` 同义词 | 除路径与美术黑话同义词外，新增 **`palette`（主辅点缀色 HEX 色板）** 与 **`specs`（标准分辨率、宽高比、RGBA 透明通道强制开关、九宫格切线 `nine_slice`、安全边距 `safe_margin_px`）** |
| **7 大记忆类型 (`kind`)** | `exclusion` / `risk` / `correction` / `decision` / `conclusion` / `feature` / `plan` | 1. `style_redline`（风格红线/打回废案正反例对比）<br>2. `pipeline_constraint`（引擎切图/图层/Alpha 硬约束）<br>3. `visual_correction`（角色/光影设定迭代勘误）<br>4. `art_decision`（主美拍板定稿与视觉锚点）<br>5. `recipe`（可复现 AI 生图配方：LoRA/Prompt/Seed/ComfyUI）<br>6. `asset_record`（入库资产台账与引擎 Prefab 引用）<br>7. `art_plan`（待产美术需求规格单） |
| **锚点与过期检测 (`Stale`)** | 基于 Python/TS AST 检查函数签名是否被修改 | **像素与元数据级锚点检测**：自动计算图片 **SHA-256 指纹**、解析 PNG `IHDR`（实际宽高、色深、RGBA 通道）与内嵌 `tEXt` 元数据；一旦资产被覆盖改尺寸或漏去背，关联记忆立即标 `STALE` |
| **AI Agent 自动化闸门 (`Hooks`)** | 改代码前强制调 `search_memory` | **双端美术闸门**：<br>① **生图前闸门（Pre-Gen Gate）**：调用生图/修图工具前强制拉取模块红线、色板与标准 Recipe；<br>② **落盘质检门（Post-Asset Validator）**：图片落盘瞬间校验分辨率、RGBA 透明通道与外框安全留白，违规立即拦截重修 |
| **可视化产物 (`HTML`)** | 知识图谱节点网络 `map.html` + 文本 `wiki` | **`art-atlas.html` 专业美术看图与记忆工作台**：支持瀑布流画廊、**棋盘格/深灰/亮白/实机四底色切换**、**Do vs. Don't 左右拖动滑杆对比**、**九宫格切线叠加预览**、**色卡点击复制 HEX** 与 **AI 配方一键复制** |

---

## 三、美术专属记忆分类体系（7 Kinds, 2 Layers）

### 第一层：防翻车与复现经验层（Lessons — AI 生图前必读，跨父子模块继承）

1. **`style_redline`（风格红线 / 废案排除）**
   - **作用**：记录曾被主美打回或 AI 高频翻车的错误方向，必须同时绑定 `approved/anchor` 正例图与 `rejected` 废案图。
   - **典型场景**：禁止赛博荧光洋红/青蓝霓虹、禁止 5 头身 Q 版比例、禁止 UI 九宫格中心拉伸区出现具象图案。
2. **`pipeline_constraint`（管线与技术规范红线）**
   - **作用**：记录游戏引擎（Unity / Unreal / Spine / Live2D）对资产的硬性物理约束。
   - **典型场景**：Spine 立绘必须拆出 6 大独立图层并扩充 12px 羽化出血位；VFX 序列帧必须采用 Premultiplied Alpha 且四周预留 16px 绝对透明安全边距防采样截断。
3. **`visual_correction`（视觉勘误与设定迭代）**
   - **作用**：当世界观或角色设定发生变更时，通过 `supersedes` 指向旧记忆 ID，记录从 V1 到 V2/V3 的改版原因（如主角单眼星盘镜片从右眼改到左眼、表情瞳色随情绪切换规则）。
4. **`art_decision`（主美拍板与视觉锚点）**
   - **作用**：确立模块的核心视觉基准（Anchor Asset），例如全局 70/20/10 色彩比例、场景 30° 等轴测与左上 45° 暖金主光方向。
5. **`recipe`（AI 生图标准配方与工作流锚点）**
   - **作用**：保存经过验证可 100% 稳定复现该模块画风的参数包：`model`（底模）、`loras`（权重配比）、`seed`、`sampler`、`controlnet`、`prompt`（固定起手词）、`negative_prompt`（防崩坏负面词）以及 `workflows/*.json` 路径。

### 第二层：资产台账与排期层（Records — 资产交付与引用追踪）

6. **`asset_record`（已验收资产台账）**
   - **作用**：记录模块内已入库资产的分辨率、SHA-256 指纹、引擎挂载位置（如 `Prefabs/Characters/Hero_Astra.prefab`），防止 AI 在修图时误覆盖已对齐骨骼锚点的正式资产。
7. **`art_plan`（待产资产需求单）**
   - **作用**：结构化列出待绘制或待 AI 生成的资产规格单（目标文件名、尺寸、透视角度、差分数量、参考锚点），完成后通过 `supersedes` 转为 `asset_record`。

---

## 四、给未来 AI 美术 Agent 的端到端工作流设计

当你在 Cursor / Claude Code / 自研 AI 美术管线中接入 `pmem-art` 时，AI Agent 的每一次生图与修图都遵循以下闭环：

```text
[用户/策划提出美术需求: "给阿斯特拉补一张惊愕表情差分，再加一个紫色品质背包弹窗底框"]
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 1: 生成前记忆召回闸门 (Pre-Generation Gate)                        │
│ AI 调用 pmem_art.py search --module character.Astra.Expressions         │
│ ↳ 自动继承父模块 character.Astra 的 7.5 头身立绘锚点与 LoRA 配方        │
│ ↳ 自动继承全局 brand.WorldStyle 的 70/20/10 青瓷色板与禁用霓虹紫红线    │
│ ↳ 读取子模块视觉勘误：惊愕表情需保持 1024x1024 RGBA 透明底              │
└─────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 2: 锁定配方调用生图工作流 (ComfyUI / SD / 图像生成脚本)            │
│ ↳ 载入 workflows/comfyui_astra_portrait_v3.json                         │
│ ↳ 自动注入正向 Prompt 模板 + Negative 防翻车词库 + IP-Adapter 锚点图    │
└─────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 3: 落盘自动质检门 (Post-Asset Validator Hook)                      │
│ 图片写入 assets/ 后，自动触发 pmem_art.py validate：                    │
│ ↳ 检查分辨率是否等于模块契约 (如 1024x1024 / 512x512)                   │
│ ↳ 检查颜色通道是否为 RGBA 透明底，外圈 safe_margin_px 像素是否全透明     │
│ ↳ 若发现违规（如生成了 768x768 RGB 白底），立即阻断并要求 AI 重新抠图扩边│
└─────────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ Step 4: 沉淀新配方与更新可视化图谱 (Stop Hook & Atlas Rebuild)          │
│ ↳ 验收通过后写入 asset_record / recipe，运行 pmem_art.py atlas          │
│ ↳ 主美打开 art-atlas.html 即可在画廊与红线看板中直观审阅最新资产        │
└─────────────────────────────────────────────────────────────────────────┘
```


---

## 五、挂载式生命周期：冷启动 / 老项目 / 持续迭代（保证项）

`pmem-art` 是**挂载式**记忆系统：可以空仓接入，也可以挂到已运行很久的美术目录上。系统**不会假装全自动魔法**，而是保证一条可重复的闭环：

> **检测新路径 → 多信号分类打分 → candidate / auto-add 模块 →（一次）accept 或高置信 ingest → search 闸门按模块召回 → record / validate → atlas**

### Mode A · 年轻 / 空项目（`init` + `bootstrap --mode young`）

| 保证 | 行为 |
| :--- | :--- |
| 空仓可挂载 | `init` 写入 `scaffold` 分类（brand/character/scene/ui/vfx/anim）+ `assets/<domain>/` 空目录 + `gate.mode=warn` |
| 自动提议，不瞎改 | 新图落入 `assets/` 后 `sync` 只写入 `candidates.json`，默认**不**静默改写 `modules.yaml` |
| 可配置浅层自动接受 | `--auto-accept-depth 2 --apply` 才把前 1–2 层路径升为 `active` |
| 年轻项目可自动归位 | `bootstrap.auto_place: true`（young 默认）时，`ingest --apply` 可直接搬进规范路径 |

### Mode B · 老项目 / 乱资产（`bootstrap --mode legacy`）

| 保证 | 行为 |
| :--- | :--- |
| 默认不移动文件 | `never_auto_move: true`；只产出 `LEGACY_BOOTSTRAP_REPORT.md` + candidates |
| 覆盖率可见 | `doctor` 显示 mapped% / orphans / 多风格冲突提示 |
| 确认后才生效 | `accept` / `place --apply` / `bootstrap --apply`（仍不移动，只升模块） |

### Mode C · 持续迭代（两端共用）

`sync` → `candidates` / `accept` → `search` / `validate` → `record` → `atlas`  
Cursor 生图额外走：`classify` / `ingest` / `classify-watch`。

---

## 六、Cursor 生图多信号自动分类与模块扩展（`classify` / `ingest`）

### 信号融合（不是单一启发式）

1. **路径 / 文件名**（`path_weight`，默认 0.25）：`assets/character/Astra/...`、`*_sheet.png` 等  
2. **用户或 Agent Prompt**（`prompt_weight`，默认 0.35）：中英关键词（立绘/九宫格/序列帧/Q版/水彩/Spine…）  
3. **图像特征**（`image_trait_weight`，默认 0.25）：宽高比、RGBA、序列帧网格（如 1024×256 → 4 帧）、UI 方图尺寸、立绘方图+透明  
4. **已有 `modules.yaml` 命中**（`module_match_weight`，默认 0.15）：路径已映射则优先 `use_existing`

输出：`domain` + `entity` + 可选 `style_fork` + `suggested_module` + **confidence** + `decision`：

| decision | 含义 |
| :--- | :--- |
| `use_existing` | 落入已有模块 |
| `auto_add_active` | 高置信度，可自动写入新 active 模块（不擦除旧模块） |
| `add_as_candidate` | 中置信度，扩展为 candidate，待 `accept` |
| `add_as_misc_candidate` | 低置信度 → `misc.<Name>`，避免静默扔错桶 |

### 风格分叉

同一角色不同画风（Q版 / 水彩 / 宣传 KV）→ 建议兄弟模块，例如 `character.阿斯特拉.Chibi`，`parent` 指向 `character.Astra` 或 `brand.WorldStyle`。

### Cursor 推荐工作流

```bash
# Agent 刚 GenerateImage 落到 .cursor/generated/xxx.png
python3 pmem_art.py classify .cursor/generated/xxx.png -p "$PROMPT"
python3 pmem_art.py ingest  .cursor/generated/xxx.png -p "$PROMPT" --apply   # 年轻项目可开 auto_place
python3 pmem_art.py classify-watch          # 扫未映射图，低置信进 misc/candidate
python3 pmem_art.py atlas
```

`classify.auto_add_modules: true` 时，**只追加**新模块键，绝不清空已有 `modules.yaml`。
