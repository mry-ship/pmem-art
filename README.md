# pmem-art

**给 Cursor / Claude Code / Codex 用的个人美术记忆 + 闭环生图系统。**  
对话里丢图、选档、出图；红线与定稿自动沉淀，下次更准。合格线统一 **`≥ 9.60`**（最多 8 轮，达标即停）。

| 文档 | 适合谁 |
| :--- | :--- |
| **本页（README）** | 30 秒搞懂：是什么、怎么接入、怎么用、效果长什么样 |
| **[使用手册 USER_MANUAL.md](USER_MANUAL.md)** | 技能全表、四档 `--scale` 细则、CLI、FAQ |
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

### 四档一句话

| 档位 | 干什么 | 停机线 |
| :--- | :--- | :--- |
| `low` | 只修瑕疵，不改机位/姿态/布局 | ≥ 9.60 |
| `medium`（默认） | 构图不动，补光影材质 | ≥ 9.60 |
| `high` | 可升级戏剧光影与张力，不换身份/画风 | ≥ 9.60 |
| `recompose` | 按你写的 `--recompose-dir` 改构图 | ≥ 9.60 |

完整权重与 Prompt 约束见手册 [第二章 / scale 专节](USER_MANUAL.md)。

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
