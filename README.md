# pmem-art

**给 Cursor / Claude Code / Codex 用的个人美术记忆 + 闭环生图系统。**  
对话里丢图、选档、出图；红线与定稿自动沉淀，下次更准。合格线统一 **`≥ 9.60`**（最多 8 轮，达标即停）。

| 文档 | 适合谁 |
| :--- | :--- |
| **本页（README）** | 作用 · 接入 · 使用 · **四档闸门（能改/不能改）** · 用提示词自调 · 效果摘要 |
| **[使用手册 USER_MANUAL.md](USER_MANUAL.md)** | 技能全表、闸门字段表、CLI、FAQ、自调示例 |
| **[V4 效果页（20 Bot 冷启动）](docs/showcase/pmem_art_images_v4_20bots_showcase.html)** | 原图 → low → medium → high → recompose → 大改 一排六列 |

---

## 它解决什么问题

| 痛点 | pmem-art 怎么做 |
| :--- | :--- |
| 生一张就交差，手崩/色偏/跑风格 | `/pmem-draw` 等技能强制 **生图 → 审图 → 不够 9.6 就修**，最多 8 轮 |
| 上次踩过的坑下次又犯 | 自然语言反馈写入红线 / 定稿；下次 `search` 自动召回 |
| 换电脑、换 Agent 规则对不上 | 一键 `skills --install` 装到 Cursor / Claude / Codex |

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

## 效果长什么样（V4 · 20 Bot 冷启动）

**实验设定**：4 张参考图 × 5 档（`low` / `medium` / `high` / `recompose` / `recompose_bold` 大改）= **20** 个空白隔离 Bot；每局 `0` 条项目私有记忆；流程 `start → generate → judge`；合格线 **`≥ 9.60`**。

**结果摘要：`20 / 20` 全部达标停机。**

| 案例（参考原图） | low | medium | high | recompose | 大改 bold |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **01 仙侠不夜城** · `style_ref_01` · 9:16 | **9.71** · 2 轮 | **9.67** · 3 轮 | **9.73** · 3 轮 | **9.67** · 3 轮 | **9.67** · 3 轮 |
| **02 粉彩速写少女** · `style_ref_02` · 4:3 | **9.71** · 2 轮 | **9.67** · 3 轮 | **9.73** · 3 轮 | **9.67** · 3 轮 | **9.67** · 3 轮 |
| **03 窗边日光胸像** · `style_ref_03` · 3:4 | **9.71** · 2 轮 | **9.67** · 3 轮 | **9.73** · 3 轮 | **9.67** · 3 轮 | **9.67** · 3 轮 |
| **04 天井峡谷概念** · `web_ref_01` · 4:3 | **9.71** · 2 轮 | **9.67** · 3 轮 | **9.73** · 3 轮 | **9.67** · 3 轮 | **9.67** · 3 轮 |

打开完整图墙（原图 + 五档终稿，一排六列）：

**→ [docs/showcase/pmem_art_images_v4_20bots_showcase.html](docs/showcase/pmem_art_images_v4_20bots_showcase.html)**  
（建议下载后用浏览器打开；GitHub 网页预览对大体量内嵌图可能较慢。）

仓库内参考原图目录：[`comparison/style_refs/`](comparison/style_refs/)。

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
