# 📘 pmem-art 画师使用手册 — 怎么在 Cursor / Codex 里越画越准

> **版本**：`v0.12+`  
> **核心理念**：日常入口就是 **Cursor / Claude Code / Codex 对话框**（外加开箱即用的 `/pmem-draw` 等 14 个斜杠技能，含简短别名共 28 个入口）。不用背 CLI、不用手写 YAML。  
> **先看总览？** → 仓库首页 [README.md](README.md)（作用 · 接入 · 使用 · V4 效果摘要）  
> **看图墙？** → [docs/showcase/pmem_art_images_v4_20bots_showcase.html](docs/showcase/pmem_art_images_v4_20bots_showcase.html)（20 Bot 冷启动 · 一排六列）

---

## 目录

1. [第一章：初始化即自动安装的 14 大美术技能](#第一章初始化即自动安装的-14-大美术技能)
2. [第二章：王牌技能 `/pmem-draw`（8轮9.6分自评收敛生图 & 垫图生图）](#第二章王牌技能-pmem-draw8轮96分自评收敛生图--垫图生图)
3. [第三章：日常对话反馈怎么变成长期记忆](#第三章日常对话反馈怎么变成长期记忆)
4. [第四章：三种项目接入方式（空项目 / 老项目 / 持续生图）](#第四章三种项目接入方式空项目--老项目--持续生图)
5. [第五章：后台自动分类与多画风分叉（水彩 / Q版 / 像素）](#第五章后台自动分类与多画风分叉水彩--q版--像素)
6. [第六章：命令与收敛追踪器参考](#第六章命令与收敛追踪器参考)
7. [第七章：常见问题 FAQ](#第七章常见问题-faq)
8. [附录 A：四档 `--scale` 细则与示例](#附录-a四档---scale-细则与示例)
9. [附录 B：V4 冷启动验收摘要](#附录-bv4-冷启动验收摘要)

---

## 第一章：初始化即自动安装的 14 大美术技能

当你运行 `python3 pmem_art.py init`（或 `python3 pmem_art.py skills --install`）时，系统会自动在项目根目录生成：

- **Cursor**：`.cursor/skills/<技能名>/SKILL.md` 与 `.cursor/commands/<技能名>.md`
- **Claude Code**：`.claude/skills/<技能名>/SKILL.md`、`.claude/commands/<技能名>.md` 与 `CLAUDE.md`
- **Codex**：`.agents/skills/<技能名>/SKILL.md` 与 `AGENTS.md`

你在对话框里敲 `/` 就能直接唤出：

| 主技能指令 | 简短别名 | 什么时候用 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | 想让 AI **自己反复打磨到 9.6 分以上**再交稿（支持纯文字或丢一张参考图） |
| **`/pmem-ui`** | **`/art-ui`** | 要 **一整套 HUD/菜单 UI Kit**（概念→组件表→九宫格→按钮多状态），对标 SpriteCook |
| **`/pmem-concept`** | **`/art-concept`** | 要 **原画 / 主视觉 / Key Art**：**强制 8轮 ≥9.6 收敛**（与 draw 同等，禁止只生一张）+ FLUX 完整句 Prompt |
| **`/pmem-icon`** | **`/art-icon`** | **内部三模式隔离**：Mode A（1024 App Icon 母版）· Mode B（24px SVG 矢量集）· Mode C（游戏透明底道具图标），关键枚强制 8 轮 ≥9.6 |
| **`/pmem-style-lock`** | **`/art-style`** | 拿到一张特别对味的样张，想把它的色板、光影、笔触锁成长期标准 |
| **`/pmem-critique`** | **`/art-check`** | 手头有一张图，想让 AI 对照历史红线按 `0–10` 五维严苛挑刺打分，并把毛病记入红线 |
| **`/pmem-variant`** | **`/art-variant`** | 角色立绘定了，想衍生 **水彩概念图 / Q版贴纸 / 表情差分 / 序列帧** 且不崩人设 |
| **`/pmem-atlas`** | **`/art-map`** | 阶段性整理散图，并刷新 `art-atlas.html` 画廊回看 |
| **`/pmem-improve`** | **`/art-improve`** | **进阶 peek**：大声读出 finish 已静默做过的自我迭代 |
| **`/pmem-coach`** | **`/art-coach`** | **进阶 peek**：短板练习计划 |
| **`/pmem-learn`** | **`/art-learn`** | **进阶 peek**：知识广度建议（finish 已静默 enqueue） |
| **`/pmem-lens-propose`** | **`/art-lens`** | **独立可选镜头包提案**：参考图 → 4 套具象机位/光影/道具方案，先选再进收敛（详见 `docs/skills/pmem-lens-propose.md`） |
| **`/pmem-clone-image`** | **`/art-clone`** | **风格克隆新主体**：Mode B ~95% 锁参考画风克隆到新题材（含角色双眼/UI双层描边门禁，强制 8 轮 ≥9.6） |
| **`/pmem-merge-ladder`** | **`/art-ladder`** | **同域合成进阶梯**：Merge-2 棋盘 L1–L8 整梯同框生成与切格审计（≥9.6） |

进步曲线 CLI：`python3 pmem_art.py progress`（无独立斜杠技能，也可用 `/pmem-improve`）。

---

## 第二章：王牌技能 `/pmem-draw`（8轮9.6分自评收敛生图 & 垫图生图）

平时让 AI 生图最大的痛点是：**生 1 张经常有硬伤（手崩、比例不对、混进赛博紫、漏画配饰），每次都要人工催它改。**  
`/pmem-draw`（别名 `/art-draw`）把「生图 → 审图打分 → 挑出不合理处 → 叠加修正再生图」做成了 **全自动收敛循环**。

### 2.1 两种输入姿势

#### 姿势 A：直接文字描述
> `/pmem-draw 生成一张青瓷幻想风格的阿斯特拉全身立绘，7.5头身，透明底`

#### 姿势 B：丢入一张图 + 文字要求（垫图解构模式）
> `/pmem-draw [拖入一张参考图] 生成一张这种构图和笔触的浮空遗迹场景气氛图`

在**姿势 B** 下，Agent 在生第 1 张图之前，必须先输出 **【参考图视觉解构报告】**：
1. 构图与透视重心
2. 主辅色板 `#HEX` 配比与光影冷暖
3. 笔触质感与边缘处理
4. 需要保留的亮点 vs 需要规避的瑕疵

### 2.2 五维严苛打分标准（满分 10.0 分，`>= 9.6` 才算合格）

现行默认按 **每维 /10** 再按档位权重合成（示例写法）：  
`构图8.6/光影8.2/透视7.8/质感8.0/风格8.4`  
五维名：**构图 · 光影色彩 · 透视与解剖 · 质感 · 规格与风格**。  
（旧写法 `风格2.2/结构2.0/光影1.7/合规1.4/还原1.3` 仍可解析为相加总分，但不作为新会话主写法。）

### 2.3 收敛规则与 5 项安全护栏（最多 8 次生图）
- **达到 `>= 9.6` 分（且未触发解剖 `< 7.5` 熔断）**：立即停止循环，当前图即为最终合格图（`high` / `recompose` 至少跑满 2 轮）。
- **`pad=auto` 智能垫图策略**：R2+ 默认开启 `pad=auto`——当上一轮涨分且 `透视与解剖 >= 7.5` 时链式垫上一轮最佳图微修；一旦掉分或 `透视与解剖 < 7.5` 立即退回 `style_ref` 原图重画，切断坏骨架遗传。
- **解剖 `< 7.5` 一票否决（熔断）**：全局停机仍以加权总分 `>= 9.6` 为准，仅当 `透视与解剖 < 7.5`（严重肢体/结构崩坏）时一票否决禁止停机；批量看板同时展示 `总分≥9.6` 与 `总分≥9.6 且 解剖≥8.5` 双指标。
- **R4 起连续 2 轮掉分 `> 0.5` 安全早停**：仅在 `round >= 4` 且连续 2 轮低于历史最高分超过 `0.5` 分时触发早停，并保底取历史最高分轮次。
- **按题材触发 R1 结构底线 + 精简回流**：仅人物/生物自动注入关节/握持/双瞳高光底线，纯空镜仅注入透视灭点与接触阴影，UI/图标跳过人体解剖词；单轮 `【回流修正】` 最多 `<= 2` 条；评分偶发失败自动重试，绝不写入泛化套话污染下一轮 Prompt。
- **满 8 次仍未达到 `9.6` 分**：停止循环，**从全部轮次中挑出综合评分最高且结构未熔断的那一张**作为最终结果，并说明残余不足。

### 2.4 结算、评分履历与记忆沉淀
默认对你展示：**每轮五维分 + 不足 + 改点**，以及结算时的**全轮评分履历** + 胜出图；系统在后台把配方写入 `recipe`、踩坑写入 `style_redline`（不旁白记忆写入）。
报告最底部会附 **本局档位合同**：五维锁定%**不是写死的**——你一句话可微调，表上显示有效%相对本档默认的 **-xx% / +yy%**（例：low 下「构图松一点」→ **75%（默认95%，-20%）**）。也可写「光影锁定降到 40%」。裁判打分加权%只作小字备注。
- 只要终稿、不要履历：`converge finish --quiet`，或说「只要终稿」。
- 不想写记忆：`converge finish --no-apply`。

---

## 第二章附：三大垂直生成技能 — 怎么用 & 原理

### `/pmem-ui`（`/art-ui`）
- **怎么用**
  - `/pmem-ui 生成一套青瓷幻想风主菜单：九宫格面板 + 按钮 normal/pressed`
  - `/pmem-ui [拖入概念图] 拆出主面板九宫格、按钮四态、进度条空/满`
- **原理**：`search` 召回 UI 红线 → **概念先行**（禁止散生硬拼）→ 透明组件表 → 九宫格+状态族+`manifest.json` → **强制 8轮 ≥9.6** 收敛写记忆。

### `/pmem-concept`（`/art-concept`）— 原画【强制 8轮 ≥9.6】
- **怎么用**
  - `/pmem-concept 画一张东方青瓷废土主视觉 Key Art，宽幅海报`
  - `/pmem-concept [拖入参考图] 同氛围角色登场 Key Art`
- **原理**：与 `/pmem-draw` **同等强制闭环**（禁止只生一张）→ 召回记忆 → FLUX 完整句 Prompt（主体靠前、排斥项正向写）→ 可选垫图解构 → `converge`（每轮展示评分履历）→ 写 `recipe`/`style_redline`（只要终稿加 `--quiet`）。

### `/pmem-icon`（`/art-icon`）— 内部三模式分节隔离
- **怎么用**
  - **Mode A（1024×1024 App Icon 母版）**：`/pmem-icon 生成 1024×1024 iOS/Android 应用图标母版，中心符号占 62%–72%，带小字号缩略可读性检查`
  - **Mode B（24px `currentColor` 一致化 SVG 矢量图标集）**：`/pmem-icon 做一套 24px Clean 导航+背包 SVG，输出 style-spec 与 preview.html`
  - **Mode C（64/128/256px 游戏透明底道具栅格图标）**：`/pmem-icon 生成一套 RPG 药水与宝箱透明底道具图标，双层外描边 + 剪影秒认`
- **原理**：在 Step 0 先判定 Mode A / Mode B / Mode C 三选一（严禁把 SVG 网格规则套在栅格图标上，也严禁把 iOS 圆角遮罩套在透明底道具上）→ 关键枚 **强制 8轮 ≥9.6** → 写记忆。

---

## 第三章：日常对话反馈怎么变成长期记忆

即使不用 `/pmem-draw`，你平时在 Cursor 里随口评一句，Agent 也会调用 `feedback` 记下来：

```bash
python3 pmem_art.py feedback "太赛博了，别这样画" -m character.Astra -a .cursor/generated/try1.png
python3 pmem_art.py feedback "这版留着" -m character.Astra -a .cursor/generated/try2.png
python3 pmem_art.py feedback "换成水彩" -m character.Astra
```

- **否定词**（太赛博 / 头太大 / 别这样画 / 漏抠） → 自动记为 **`style_redline`（红线）**
- **肯定词**（这版留着 / 就这个 / 定稿 / 过了） → 自动记为 **`recipe`（定稿配方）**
- **调整词**（换成水彩 / 改成Q版 / 修一下） → 自动记为 **`visual_correction`（勘误 + 画风分叉）**
- **定调词**（以后都用… / 统一用…） → 自动记为 **`art_decision`（审美拍板）**

---

## 第四章：三种项目接入方式（空项目 / 老项目 / 持续生图）

### 4.1 空项目冷启动
```bash
python3 pmem_art.py init --name "Project-Celadon"
python3 pmem_art.py bootstrap --mode young --apply
```

### 4.2 老项目无损挂载（绝不乱移旧文件）
```bash
python3 pmem_art.py bootstrap --mode legacy --roots Art Content assets
python3 pmem_art.py accept --all
python3 pmem_art.py skills --install
```

### 4.3 持续生图自动分类入库
```bash
python3 pmem_art.py ingest .cursor/generated/new.png -p "角色Astra 水彩 概念图" --apply
```

---

## 第五章：后台自动分类与多画风分叉（水彩 / Q版 / 像素）

系统在后台维护 `brand` / `character` / `scene` / `ui` / `vfx` / `anim` 六大领域与 `misc` 候选池：
- 同一个角色 `character.Astra`，当你说「换成水彩」或生成水彩概念图时，会自动归入子模块 **`character.Astra.Watercolor`**（继承 `character.Astra` 的人设锚点，但独立存放且不强制要求透明底）。
- 置信度高（`>= 0.78`）自动激活模块；置信度中等或偏低则保持 **`candidate`（候选）**，绝不静默污染正式模块。

---

## 第六章：命令与收敛追踪器参考

| 命令 | 说明 |
| :--- | :--- |
| `python3 pmem_art.py skills --install` | 安装/刷新 `.cursor`、`.claude`、`.agents` 下的 14 项技能与 28 个斜杠命令入口 |
| `python3 pmem_art.py skills --list` | 查看所有内置技能列表 |
| `python3 pmem_art.py converge start -g "<目标>" -m <模块> [--scale medium] [--ref-image <图> --ref-analysis "<解构>"]` | 开启一轮最多 8 次、`>=9.6` 分的收敛生图会话 |
| `python3 pmem_art.py converge generate --round <i> -i <图> -p "<Prompt>"` | **仅生图登记**（禁止带 score/dims；与 judge 必须分两步） |
| `python3 pmem_art.py converge judge --round <i> -i <图> --dims "..." --strengths "..." --defects "..." --next-fix "..."` | **独立审图**：五维打分、亮点、不合理处与下一轮修正（须先有 generate） |
| `python3 pmem_art.py converge finish` | 结算达标图或 8 轮最高分图；**默认写入记忆并打印评分履历**（`--no-apply` 可跳过；`--quiet` 只要一行结论） |
| `python3 pmem_art.py feedback "<原话>" -m <模块> [-a <图>]` | 把画师自然语言评价沉淀为记忆 |
| `python3 pmem_art.py search -m <模块>` | 召回该模块（含父模块）的红线、定稿与色板 |
| `python3 pmem_art.py ingest <图> -p "<说明>" --apply` | 四信号分类并归档图片 |
| `python3 pmem_art.py atlas` | 可选：编译生成 `art-atlas.html` 可视化图谱 |

---

## 第七章：常见问题 FAQ

**Q1：如果连生 8 张图都没有达到 9.6 分怎么办？**  
A：到了第 8 轮仍未达 9.6 分时，`converge finish` 会自动停止循环，从 1~8 轮里挑出**综合评分最高**的那一张作为阶段最优交付图；默认给你全轮评分履历（不足/改点）+ 胜出图。只要终稿时加 `--quiet`。

**Q2：丢入一张图让 `/pmem-draw` 生成时，它会怎么处理那张图？**  
A：它会先做 **Step 0 参考图深度解构**（分析构图、提取主辅色 HEX、判断光影与笔触、识别头身结构），把解构结论记入收敛会话基准，然后带着这份基准进入 1~8 轮自评收敛循环。

**Q3：以后升级了 `pmem-art`，怎么刷新已安装项目的技能文件？**  
A：在项目根目录运行 `python3 pmem_art.py skills --install` 即可一键无损刷新 `.cursor`、`.claude`、`.agents` 下的全部技能定义。


---

## v0.11 连续自我迭代（能力 + 广度）

```bash
python3 pmem_art.py converge start -g "…" -m <模块>          # Warm-Start
python3 pmem_art.py converge start -g "…" -m <模块> --mode fast
python3 pmem_art.py improve run && python3 pmem_art.py progress
python3 pmem_art.py coach
python3 pmem_art.py learn suggest && python3 pmem_art.py learn accept --all
```

闭环（v0.13 履历可见）：`warm-start → 8×≥9.6（每轮展示评分/不足/改点）→ finish 打印履历 + 记忆静默自动驾驶 → 最多一行小提示 → 越用越好`；只要终稿用 `--quiet`；`improve/coach/learn/progress` 为进阶 peek。

---

## 附录 A：四档 `--scale` 细则与示例

> **首页已有闸门总表**：[README · 四档闸门](README.md#四档闸门每档允许变什么--禁止变什么)。本附录补「怎么自己调」与 CLI。

两大驱动：

1. **模型自动分析收敛**：`low` / `medium` / `high` — 自主诊断缺陷、生成 `next_fix`，加权分 **`>= 9.60` 即停**。  
2. **玩家定向改构图**：`recompose` + `--recompose-dir` — 按你指定的新机位/布局改，仍锁画风与身份。

### A.1 闸门字段（与源码一致）

源文件：`skills_kit/prompt_scale.py` → `CONVERGE_SCALE_PROFILES`。

| 档位 | `max_prompt_delta` | 最早停机 | 允许机位 | 允许姿态 | 允许改布局 | 允许大改光影 | 硬锁 / 保留集 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `low` | ≤20% vs 首轮 | 1 | ❌ | ❌ | ❌ | ❌ | 姿态/机位一条 + 画风 + 身份 |
| `medium` | ~40% / 累计 60% | 1 | ❌ | ✅（小幅） | ✅（局部） | ✅ | 锁机位；禁整体 recompose / 大改元素清单 |
| `high` | ≤80% / 累计 90% | **2** | ✅ | ✅ | ✅ | ✅ | 媒介基因 + `no_identity_swap`（可叙事，不换主体） |
| `recompose` | ≤85% / 累计 95% | **2** | ✅（按方向） | ✅ | ✅ | ✅ | 画风 + 身份 + **目标机位=`--recompose-dir`**（与 bold 拆开） |

### A.2 某一档不符合预期时：用提示词覆盖闸门（推荐）

不必先改源码。在斜杠命令后追加约束，Agent 会写进本轮 Prompt / `next_fix`：

| 场景 | 示例提示词 |
| :--- | :--- |
| low 修不够 | 「low 闸门内允许修衣褶高光与金属反光，仍禁止改机位姿态」 |
| medium 光影弱 | 「medium：允许更强体积光与雾层，仍禁止换镜头」 |
| high 构图乱动 | 「high：禁止改机位与布局，只升级光影材质」 |
| recompose 跑偏 | 「必须保留原图 X；禁止出现 Y；严格执行 recompose-dir」 |
| 想长期生效 | `python3 pmem_art.py feedback "以后 medium 禁止改发色" -m <模块>` |

全局改默认闸门（权重 / 改动上限 / forbidden 列表）：改 `prompt_scale.py` 后 `python3 pmem_art.py skills --install`。

```text
/pmem-draw --scale low @comparison/style_refs/style_ref_02_pastel_sketch.png 只修五指与球鞋透视
/pmem-draw --scale medium @comparison/style_refs/style_ref_03_sunlit_portrait.png 补轮廓光与空气微尘；禁止改机位
/pmem-concept --scale high @comparison/web_refs/web_ref_01_concept_ishtar.png 升级丁达尔神光；锁身份与画风
/pmem-draw --scale recompose --recompose-dir "改为天台远眺海港全景" @comparison/style_refs/style_ref_02_pastel_sketch.png
```

生图与审图必须分两步（Skill 会自动跑）：

```bash
python3 pmem_art.py converge generate --id <sid> --round 1 -i out.jpg -p "<prompt>"
python3 pmem_art.py converge judge    --id <sid> --round 1 -i out.jpg --dims "构图9.2/光影9.1/透视9.0/质感9.0/风格9.2" --defects "..." --next-fix "..."
python3 pmem_art.py converge finish   --id <sid>   # 默认写记忆并打印评分履历；只要终稿加 --quiet
```

---

## 附录 B：V4 冷启动验收摘要

来源：[docs/showcase/pmem_art_images_v4_20bots_showcase.html](docs/showcase/pmem_art_images_v4_20bots_showcase.html)

- **规模**：4 案例 × 5 档（含 `recompose_bold` 大改）= **20** Bot  
- **条件**：每 Bot 独立空目录、项目私有记忆 = 0、三步分离、画幅/垫图继承校验  
- **结果**：**20 / 20** 达到 `≥ 9.60` 停机  
- **首页图墙 + 分数进度**：见 [README.md §效果长什么样](README.md)（原图与五档终稿、R1→终分轨迹直接嵌在 README）
- 逐张 MD5 / 长文视觉核验仍以该 HTML 为准。
