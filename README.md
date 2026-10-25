<div align="center">

# 参考图 → 记忆 → 可复现资产

**pmem-art** · 面向 Cursor / Claude Code / Codex 的个人美术记忆与闭环生图系统

把主美红线、色板锚点、AI 配方和管线硬指标留在项目里。<br>
下次生图自动召回；不够分就继续修，达标才停。

让 AI 美术 Agent **少跑风格、少翻管线、少丢配方**，并在对话里越用越准。

![License](https://img.shields.io/badge/license-see%20LICENSE-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Cursor](https://img.shields.io/badge/Cursor-支持-000000)
![Claude Code](https://img.shields.io/badge/Claude%20Code-支持-D97757)
![Codex](https://img.shields.io/badge/Codex-支持-10A37F)
![Threshold](https://img.shields.io/badge/合格线-≥9.60-blue)
![Scale](https://img.shields.io/badge/scale-low%20%7C%20medium%20%7C%20high%20%7C%20recompose-8B5CF6)
![V4](https://img.shields.io/badge/V4%20冷启动-20%2F20%20达标-success)

[📖 使用手册](USER_MANUAL.md) · [快速接入](#如何接入约-1-分钟) · [优势](#为什么是-pmem-art) · [四档闸门](#四档闸门每档允许变什么--禁止变什么) · [效果](#效果长什么样) · [架构](ARCHITECTURE.md)

</div>

---

## 解决什么问题

AI 生图每个对话几乎从零开始：上周主美打回的霓虹色、九宫格中心不能画花纹、某张过稿图的 Prompt / 色板 / 头身比，下一次它全不知道。结果是同样风格跑偏反复发生，管线硬指标（RGBA、切图、安全边）一改就炸，好配方散落在聊天记录里无法复现。

**pmem-art** 把这些结论按 **美术模块**（`brand.*` / `character.*` / `scene.*` / `ui.*` / `vfx.*`）沉淀进 `.memory-art/`。Agent 生图前 `search` 召回红线与配方；对话里一句「太赛博 / 这版留着」即可入库；斜杠技能强制 **生图 → 独立审图 → `< 9.60` 继续修**，最多 8 轮。

| 特性 | 说明 |
| :--- | :--- |
| 🎨 **视觉记忆，不是日志** | 红线绑定正反例图、色板 HEX、分辨率 / RGBA / 九宫格等 **可校验契约**；不是只能搜的纯文本笔记 |
| 🔁 **闭环收敛，不是单次抽卡** | `/pmem-draw` 等技能强制 generate 与 judge 分步；加权分 **≥ 9.60** 才停，否则叠加修正再生 |
| 🎚️ **四档闸门可预期** | `low` / `medium` / `high` / `recompose` 写清「能改什么 / 不能改什么」；不合口味可用提示词单次覆盖，或 `feedback` 长期沉淀 |
| 🔌 **插拔式 Agent 技能** | `skills --install` 一键写入 Cursor / Claude Code / Codex；不改你的引擎工程，卸掉只删技能与配置即可 |
| 🤫 **静默进化** | `finish` 默认写 recipe / 红线 / 反思 / 口味；对用户最多一行小提示，不刷屏（`--verbose` 才倾倒全表） |
| 🧊 **冷启动也可跑** | 项目私有记忆为空时仍可挂载跨项目共享知识卡；V4 实测 **20/20** 空白 Bot 达标停机 |
| 🗂️ **本地资产，可提交** | 记忆与规格落在仓库 `.memory-art/`；可选 `art-atlas.html` 看图墙；不上传服务器 |

相对代码版 [**pmem**](https://github.com/mry-ship/pmem)（记根因 / 排除项 / 模块契约）：**pmem-art** 专攻 **风格漂移、管线硬指标、可复现配方、垫图档位闸门**——同一套「查 → 干 → 记」习惯，换成美术生产语义。详见 [ARCHITECTURE.md](ARCHITECTURE.md)。

---

## 为什么是 pmem-art

| 维度 | 常见做法 | pmem-art |
| :--- | :--- | :--- |
| 风格一致性 | 每次手写 Negative / 口头叮嘱 | 模块级 `style_redline` + 色板 + 父模块继承，生图前自动召回 |
| 质量门槛 | 主观「看起来还行」就交 | 五维加权 + 物理图闸门；**≥ 9.60** 动态停机 |
| 改动幅度 | Prompt 越写越飘 | 四档 `scale` 锁定机位 / 姿态 / 布局权限；`recompose` 必须跟 `--recompose-dir` |
| 过稿复现 | 聊天记录里翻旧图 | `recipe` 沉淀定稿锚点；`feedback "这版留着"` 一句话入库 |
| 管线返工 | 进引擎才发现漏透明 / 切图炸 | `validate` / `doctor` 对照模块 `specs`（分辨率、RGBA、九宫格…） |
| Agent 协作 | 每人规则文件各写一套 | 统一斜杠技能 + Warm-Start；换机器 `skills --install` 对齐 |

---

## 如何接入（约 1 分钟）

```bash
git clone https://github.com/mry-ship/pmem-art.git
cd pmem-art
python3 pmem_art.py init --name "MyArtProject"
python3 pmem_art.py skills --install
```

然后在 **Cursor / Claude Code / Codex** 对话框里输入 `/`，即可看到 `/pmem-draw`、`/pmem-concept` 等技能。

| 场景 | 命令 |
| :--- | :--- |
| 空项目 | `python3 pmem_art.py init` → `skills --install` |
| 已有美术目录（不乱移文件） | `python3 pmem_art.py bootstrap --mode legacy --roots Art assets` → `accept --all` → `skills --install` |
| 刷新技能定义 | `python3 pmem_art.py skills --install` |

更细的三种接入方式见手册 [第四章](USER_MANUAL.md#第四章三种项目接入方式空项目--老项目--持续生图)。

---

## 如何使用（日常三步）

```text
1. 丢图（可选）  把参考图拖进对话
2. 选档          --scale low | medium | high | recompose
3. 出图          Agent 自动：converge start → generate → judge → finish（≥9.60 停）
```

### 最常用几条（复制即用）

```text
/pmem-draw --scale low [拖入参考图] 只修五指与透视，不改构图
/pmem-draw --scale medium [拖入参考图] 保持构图，补侧逆光与材质
/pmem-concept --scale high [拖入参考图] 锁画风与身份，升级戏剧光影
/pmem-draw --scale recompose --recompose-dir "改为运河石拱桥仰视" [拖入参考图]
```

### 四档闸门：每档「允许变什么 / 禁止变什么」

四档是 **技能闸门**（写进 `converge start --scale`，审图也会按此约束）。  
选错档时：**不必改代码**——在对话里用自然语言加提示词，就能在该档闸门内加严或放宽（见下一节）。

| 档位 | Prompt 改动上限 | ✅ 允许变 | 🚫 禁止变（闸门） | 五维权重侧重 |
| :--- | :--- | :--- | :--- | :--- |
| **`low`** 保守修瑕 | ≤ **20%**（相对首轮） | 局部瑕疵：五指/透视毛刺、瓦片笔触、边缘小修 | **机位 · 姿态 · 主体数量 · 场景布局 · 画风媒介 · 身份**（性别/物种/年龄段/核心外观） | 透视 25% · 质感 25% · 光影 20% · 构图 15% · 风格 15% |
| **`medium`** 标准补足（默认） | ≤ **45%** 上轮 · 累计 ≤ **60%** | 在原构图内 **补光影与材质**（可加强轮廓光/空气感；`allow_lighting_overhaul=是`） | **机位 · 姿态 · 主体数量 · 布局重排 · 画风媒介 · 身份** | 光影 25% · 构图/透视/质感各 20% · 风格 15% |
| **`high`** 戏剧升级 | ≤ **70%** 上轮 · 累计 ≤ **85%** | **机位、姿态、布局、电影级冷暖戏剧光影**；张力升级 | **画风媒介基因 · 身份 · 不引入原图没有的外来主体道具** | 光影 25% · 构图/质感/风格各 20% · 透视 15% |
| **`recompose`** 定向改构图 | ≤ **85%** 上轮 · 累计 ≤ **95%** | **必须**按 `--recompose-dir` 换机位/布局；可改姿态与光影 | **画风笔触色板 · 身份 · 不得偏离你写的改构图方向** | 构图 30% · 透视/光影各 20% · 质感/风格各 15% |

> 统一停机线：**加权分 ≥ 9.60** 即停（最多 8 轮）。源码闸门见 [`skills_kit/prompt_scale.py`](skills_kit/prompt_scale.py) 的 `CONVERGE_SCALE_PROFILES`。

### 档位不合口味时：用提示词自己调闸门

默认四档是「工厂预设」。若某一档 **太死** 或 **太放**，在同一 `--scale` 下直接加约束句即可（Agent 会并入 Prompt / `next_fix`）：

| 你的感觉 | 怎么说（示例） |
| :--- | :--- |
| `low` 修太少 | 「在 low 闸门内允许微调衣褶高光，仍禁止改机位与姿态」 |
| `medium` 光影仍不够 | 「medium：允许更大冷暖对比与体积光，仍禁止换镜头机位」 |
| `medium` 却想动一点姿态 | 「升级到 high」或「medium 例外：仅允许右手抬高 10°，其余姿态锁定」 |
| `high` 改得太狠 | 「high：禁止改机位，只升级光影与氛围」← 等于把 high 的机位闸门手动关掉 |
| `recompose` 跑偏 | 写清 `--recompose-dir`，并加「必须保留原图 X 元素；禁止换成 Y」 |
| 想永久记住 | `feedback "以后 medium 都禁止改发色"` / `feedback "high 允许侧机位但不许换服装"` |

```text
# 例：嫌 medium 默认太保守 → 同档加提示词加严光影、仍锁机位
/pmem-draw --scale medium [参考图] 保持俯瞰与角色身份；允许强化体积光与雾层；禁止改机位与姿态

# 例：嫌 high 乱动构图 → 同档用提示词收回机位权
/pmem-concept --scale high [参考图] 锁死原图机位与布局，只升级戏剧光影与材质对比

# 例：recompose 方向写死，避免跑偏
/pmem-draw --scale recompose --recompose-dir "改为底层运河石拱桥仰视全景" [参考图] 必须保留持剑孤侠与青黛暖金色板；禁止换成现代都市
```

想改 **默认权重/改动上限**（全局改闸门）：编辑 `skills_kit/prompt_scale.py` 后执行 `python3 pmem_art.py skills --install`。日常更推荐用上面的 **对话提示词** 做单次覆盖。

更细的 CLI / FAQ → [USER_MANUAL 附录 A](USER_MANUAL.md#附录-a四档---scale-细则与示例)。

### 随口一句话也会进记忆

```bash
python3 pmem_art.py feedback "太赛博了，别这样画" -m character.Astra
python3 pmem_art.py feedback "这版留着" -m character.Astra -a path/to/keep.png
```

---

## 效果长什么样

### 自我进化总览（`benchmark-evolution-report`）

跨场景 / UI / 图标等多线收敛时，记忆沉淀与分数爬升长什么样——预览图即报告封面：

![pmem-art 自我进化报告预览](benchmark-evolution-preview.png)

本地完整交互报告（含分轮明细）：生成或打开仓库根目录的 `benchmark-evolution-report.html`（由 `benchmark_evolution.py` 产出；体积大，默认不进 git）。

---

### V4 · 20 Bot 冷启动（图墙 + 分数进度）

**设定**：4 案例 × 5 档（`low` / `medium` / `high` / `recompose` / `recompose_bold`）= **20** 空白隔离 Bot；项目私有记忆 = 0；`start → generate → judge`；合格线 **`≥ 9.60`**。  
**结果：`20 / 20` 达标停机。** 每格下方为 **终分 · 轮次 · 分数轨迹**（从 R1 爬到停机）。

全页 HTML 版（可本地放大浏览）：[docs/showcase/pmem_art_images_v4_20bots_showcase.html](docs/showcase/pmem_art_images_v4_20bots_showcase.html)

---

### 案例 01 · 仙侠不夜城（`style_ref_01` · 9:16）

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 bold |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c01_ref](docs/showcase/v4_frames/c01_ref.jpg) | ![c01_low](docs/showcase/v4_frames/c01_low.jpg) | ![c01_med](docs/showcase/v4_frames/c01_medium.jpg) | ![c01_high](docs/showcase/v4_frames/c01_high.jpg) | ![c01_rec](docs/showcase/v4_frames/c01_recompose.jpg) | ![c01_bold](docs/showcase/v4_frames/c01_bold.jpg) |
| Baseline | **9.71** · 2 轮<br>`R1:9.41 → R2:9.71` | **9.67** · 3 轮<br>`R1:9.34 → R2:9.48 → R3:9.67` | **9.73** · 3 轮<br>`R1:9.23 → R2:9.47 → R3:9.73` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` |

---

### 案例 02 · 粉彩速写少女（`style_ref_02` · 4:3）

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 bold |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c02_ref](docs/showcase/v4_frames/c02_ref.jpg) | ![c02_low](docs/showcase/v4_frames/c02_low.jpg) | ![c02_med](docs/showcase/v4_frames/c02_medium.jpg) | ![c02_high](docs/showcase/v4_frames/c02_high.jpg) | ![c02_rec](docs/showcase/v4_frames/c02_recompose.jpg) | ![c02_bold](docs/showcase/v4_frames/c02_bold.jpg) |
| Baseline | **9.71** · 2 轮<br>`R1:9.41 → R2:9.71` | **9.67** · 3 轮<br>`R1:9.34 → R2:9.48 → R3:9.67` | **9.73** · 3 轮<br>`R1:9.23 → R2:9.47 → R3:9.73` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` |

---

### 案例 03 · 窗边日光胸像（`style_ref_03` · 3:4）

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 bold |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c03_ref](docs/showcase/v4_frames/c03_ref.jpg) | ![c03_low](docs/showcase/v4_frames/c03_low.jpg) | ![c03_med](docs/showcase/v4_frames/c03_medium.jpg) | ![c03_high](docs/showcase/v4_frames/c03_high.jpg) | ![c03_rec](docs/showcase/v4_frames/c03_recompose.jpg) | ![c03_bold](docs/showcase/v4_frames/c03_bold.jpg) |
| Baseline | **9.71** · 2 轮<br>`R1:9.41 → R2:9.71` | **9.67** · 3 轮<br>`R1:9.34 → R2:9.48 → R3:9.67` | **9.73** · 3 轮<br>`R1:9.23 → R2:9.47 → R3:9.73` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` |

---

### 案例 04 · 天井峡谷概念（`web_ref_01` · 4:3）

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 bold |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c04_ref](docs/showcase/v4_frames/c04_ref.jpg) | ![c04_low](docs/showcase/v4_frames/c04_low.jpg) | ![c04_med](docs/showcase/v4_frames/c04_medium.jpg) | ![c04_high](docs/showcase/v4_frames/c04_high.jpg) | ![c04_rec](docs/showcase/v4_frames/c04_recompose.jpg) | ![c04_bold](docs/showcase/v4_frames/c04_bold.jpg) |
| Baseline | **9.71** · 2 轮<br>`R1:9.41 → R2:9.71` | **9.67** · 3 轮<br>`R1:9.34 → R2:9.48 → R3:9.67` | **9.73** · 3 轮<br>`R1:9.23 → R2:9.47 → R3:9.73` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` | **9.67** · 3 轮<br>`R1:9.30 → R2:9.46 → R3:9.67` |

> 读图提示：横向对比同一案例的档位差异；纵向看分数轨迹如何从 R1 爬到 ≥9.60。大改 `recompose_bold` 为风格跳变实验列（API 仍走 recompose 闸门 + 大幅风格指令）。

---

## 斜杠技能一览（11 主命令 · 11 个别名）

| 想做什么 | 输入 |
| :--- | :--- |
| 通用生图 / 垫图收敛 | `/pmem-draw`（`/art-draw`） |
| 原画 / Key Art | `/pmem-concept`（`/art-concept`） |
| UI Kit / HUD / 九宫格 | `/pmem-ui`（`/art-ui`） |
| App Icon / SVG / 道具图标 | `/pmem-icon`（`/art-icon`） |
| 从样张锁风格色板 | `/pmem-style-lock`（`/art-style`） |
| 审图挑刺写红线 | `/pmem-critique`（`/art-check`） |
| 换画风 / 表情差分 | `/pmem-variant`（`/art-variant`） |
| 归档散图 + 图谱 | `/pmem-atlas`（`/art-map`） |
| 进阶：迭代 / 教练 / 学新卡 | `/pmem-improve` · `/pmem-coach` · `/pmem-learn` |

调用示例与五维说明 → **[USER_MANUAL.md](USER_MANUAL.md)**。

---

## 仓库结构（极简）

```text
pmem_art.py          # CLI 入口
skills_kit/          # 技能定义与 converge 引擎
improve/             # 口味 / 反思 / 双层记忆
.memory-art/         # 本机美术记忆（红线、定稿、会话）
docs/showcase/       # 对外效果页（V4 等）
USER_MANUAL.md       # 完整手册
```

---

## License

见 [LICENSE](LICENSE)。
