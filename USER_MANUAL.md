# 📘 pmem-art 画师使用手册 — 怎么在 Cursor / Codex 里越画越准

> **版本**：`v0.13+`  
> **核心理念**：日常入口就是 **Cursor / Claude Code / Codex 对话框**（10 个技能，每个只有一个 `/pmem-` 名字。没点名具体技能走 `/pmem-agent`）。不用背 CLI、不用手写 YAML。  
> **先看总览？** → 仓库首页 [README.md](README.md)（作用 · 接入 · 10 个技能 · 效果图墙）  
> **技能流程图（一眼看懂）？** → [第一章附](#第一章附工作流程图一眼看懂) · 网页点选版 [docs/skills/flows.html](docs/skills/flows.html)  
> **看图墙？** → [README · 效果长什么样](README.md#效果长什么样) · [V8 全页](docs/showcase/pmem_art_images_v8_20bots_showcase.html)

---

## 目录

1. [第一章：初始化即自动安装的 10 个美术技能](#第一章初始化即自动安装的-10-个美术技能)
2. [第一章附：工作流程图（一眼看懂）](#第一章附工作流程图一眼看懂)
3. [第二章：王牌技能 `/pmem-draw`（4轮9.6分自评收敛生图 & 垫图生图）](#第二章王牌技能-pmem-draw4轮96分自评收敛生图--垫图生图)
4. [第三章：日常对话反馈怎么变成长期记忆](#第三章日常对话反馈怎么变成长期记忆)
5. [第四章：三种项目接入方式（空项目 / 老项目 / 持续生图）](#第四章三种项目接入方式空项目--老项目--持续生图)
6. [第五章：后台自动分类与多画风分叉（水彩 / Q版 / 像素）](#第五章后台自动分类与多画风分叉水彩--q版--像素)
7. [第六章：命令与收敛追踪器参考](#第六章命令与收敛追踪器参考)
8. [第七章：常见问题 FAQ](#第七章常见问题-faq)
9. [附录 A：四档 `--scale` 细则与示例](#附录-a四档---scale-细则与示例)
10. [附录 B：V4 冷启动验收摘要](#附录-bv4-冷启动验收摘要)

> **流程图网页版（可点选切换）**：[docs/skills/flows.html](docs/skills/flows.html)

---

## 第一章：初始化即自动安装的 10 个美术技能

玩家没点名具体技能时走 `/pmem-agent`。总控固定 2 轮：第 1 轮写出需求，第 2 轮查合理性、缺漏和理解错误。可默认的路径/版式/同范围写入定稿；只有交付类型或身份题材硬歧义才打回。定稿后把定稿和每一张图交给下面某一支（整页对比可依次多支），并写明选了哪一支。点名了某一条，就直接走那一条。每个技能只有下面这一个名字。

当你运行 `python3 pmem_art.py init`（或 `python3 pmem_art.py skills --install`）时，系统会自动在项目根目录生成：

- **Cursor**：`.cursor/skills/<技能名>/SKILL.md` 与 `.cursor/commands/<技能名>.md`
- **Claude Code**：`.claude/skills/<技能名>/SKILL.md`、`.claude/commands/<技能名>.md` 与 `CLAUDE.md`
- **Codex**：`.agents/skills/<技能名>/SKILL.md` 与 `AGENTS.md`

你在对话框里敲 `/` 就能直接唤出：

| 技能指令 | 什么时候用 |
| :--- | :--- |
| **`/pmem-agent`** | 总控。没点名具体技能时走这一条。固定 2 轮；可默认则默认，硬歧义才打回。对比展陈可依次点名多支。不生图；结算格式仍是那一支自己的 |
| **`/pmem-draw`** | 生图。普通图、原画、克隆、变体或镜头包，打磨到 9.6。要锁某一支，把「原画 / 克隆 / 变体 / 镜头包」写在句子里 |
| **`/pmem-ui`** | 一整套 HUD/菜单。判成界面才走 |
| **`/pmem-icon`** | 图标三档不混：桌面母版、线性 SVG、道具格 |
| **`/pmem-merge-ladder`** | 合成梯。先用 3 稿把升级链和画风定清楚，再一档一张正方形。同框只是预览 |
| **`/pmem-prompt`** | 按交付类型扩成 2～4 套提示词。不生图，点选后再交给对应技能 |
| **`/pmem-style-lock`** | 从样张锁色板、光影、禁用词。不进自动生图 |
| **`/pmem-critique`** | 只审图，并可以把毛病记入红线 |
| **`/pmem-atlas`** | 整理散图，刷新 `art-atlas.html` |
| **`/pmem-coach`** | 进步、短板、知识合成一条。说「进步」或「知识」就看那一份。知识卡要你说收下才写入 |

镜头包点选前不生图。有参考但没说新题材时，不会走进克隆。

进步曲线 CLI：`python3 pmem_art.py progress`（也可用 `/pmem-coach`，说「进步」）。

---

## 第一章附：工作流程图（一眼看懂）

> 原画、克隆、变体、镜头包已经收进 `/pmem-draw`。下面仍按那一支合同画流程，不再是互相竞争的入口。合成梯以「先过关系、再一档一张」为准，同框不是成品。细则以各 `SKILL.md` 为准。  
> 可交互点选版：[docs/skills/flows.html](docs/skills/flows.html)

### 先分三类

| 类型 | 技能 | 一句话 |
| :--- | :--- | :--- |
| **总控** | `/pmem-agent` | 没点名时先把需求定稳；可默认则默认，硬歧义才打回。单交付一支，整页对比可依次多支 |
| **生图** | draw（含原画、克隆、变体、镜头包）· ui · icon · 合成梯 | 认成一支再做。生图→打分→不够就改，最多 4 轮 |
| **不生图** | prompt · style-lock · critique · atlas | 写提示词、锁风格、只审、归档 |
| **进阶偷看** | coach（含进步、知识） | 日常 `finish` 已静默跑过；知识卡要说收下才写入 |

### `/pmem-agent` — 总控

没点名具体技能时走这一条。总控自己不生图。点名了界面、图标、合成梯、原画、克隆、变体、镜头包、锁风格、审图、归档或教练，就直接读那一支。

```mermaid
flowchart TD
  A[第 1 轮写出需求句] --> B[第 2 轮查合理性、缺漏、理解错误]
  B --> C{没有硬不确定且话和图对得上?}
  C -->|否| R[硬歧义才打回 · 一次一处]
  C -->|是| D[定稿 + 每一张图 + 技能现稿]
  D --> E[选一支或依次多支]
  E --> F[按那一支执行 · 图不收成一张]
  F --> G[结算格式仍是那一支的]
```

第 1 轮写出交付物、每张图锁什么、不锁什么。路径/版式/「再跑一遍」同范围等可默认项写成「默认：…」进定稿；只有交付类型互斥、身份题材会做错、话图矛盾才标「还不确定」。第 2 轮只查这三件：合不合理、漏了什么、有没有理解错；并把误标的可默认项改成默认。定稿是第 2 轮。打回时只写三行：每一轮的需求句、硬不确定是哪一处、需要拍板的那一个问题。

第二段会 `converge start` 时，先把第一段每一轮用 `converge discuss` 记进同一会话，过程板上能看到需求是怎么定下来的。多张图全部写入 `--reference-image-paths`，第一张对齐交付物的宽高比，其余按定稿顺序跟在后面。生成轮若只能垫一张，垫宽高比对齐的那张；打分时仍把成图和每一张参考图并排看。

---

### 共享收敛环（普通图、原画、克隆、变体、界面、图标都套这层）

```mermaid
flowchart LR
  A[查记忆 search] --> B[converge start]
  B --> C[生 1 张]
  C --> D[五维 judge]
  D -->|≥9.6 且护栏过| E[停 · 胜出]
  D -->|<9.6 且未满 4| F[≤2 条部位修正]
  F --> C
  D -->|满 4 轮| G[Best-of-4]
  E --> H[finish 履历可见]
  G --> H
  H --> I[记忆静默写入]
```

要点：评分履历对你可见，结算另给一张可点开的过程板；`recipe` / 红线 / taste 在后台静默写，不旁白。

---

### `/pmem-draw` — 通用生图

```mermaid
flowchart TD
  S{有参考图?} -->|是| R0[Step0 视觉解构]
  S -->|否| R1
  R0 --> R1[search + Warm-Start]
  R1 --> G[生 1 张 · pad=auto]
  G --> J[五维打分 + 展示不足/改点]
  J -->|≥9.6| OK[定稿]
  J -->|解剖熔断 / 未达标| FIX[部位级修正]
  FIX --> G
  J -->|满 4 轮| BEST[取历史最高]
  OK --> F[finish]
  BEST --> F
```

---

### 原画（写在 `/pmem-draw` 里）— Key Art

```mermaid
flowchart LR
  A[可选垫图解构] --> B[Warm-Start]
  B --> C[FLUX 完整句 Prompt]
  C --> D[同 draw 的 4×≥9.6]
  D --> E[finish]
```

与 draw 同等强制闭环；差别在 **完整句 Prompt + 叙事构图侧重**。

---

### `/pmem-ui` — UI Kit

```mermaid
flowchart TD
  A[定屏幕规格 + search] --> B[概念先行 4×≥9.6]
  B --> C[透明组件表]
  C --> D[九宫格 + manifest]
  D --> E[关键件可再 converge]
  E --> F[ingest / feedback]
```

禁止各控件散生再硬拼；概念未过线不进组件表。

---

### `/pmem-icon` — 三模式

```mermaid
flowchart TD
  IN[入口 /pmem-icon] --> M{选模式}
  M --> A[A · 1024 App Icon 母版]
  M --> B[B · SVG 集：spec→分批→preview]
  M --> C[C · 道具栅格 64/128/256]
  A --> K[关键枚可选 4×≥9.6]
  B --> K
  C --> K
  K --> OUT[沉淀 style-spec]
```

三模式严禁串味（别把 SVG 规则套到道具 PNG）。

---

### 克隆（写在 `/pmem-draw` 里）— ~95% 锁风克隆

```mermaid
flowchart TD
  A[圣经 + 新题材 Brief] --> B{Mode}
  B -->|A 零参考| G
  B -->|B 有参考| P[每轮必须垫风格参考]
  P --> G[生图]
  G --> J[五维 · 眼/chrome/尺度硬门]
  J -->|≥9.6| D[交付 + 稳测连续 3 组]
  J -->|未过| F[叠加修正写进提示词 · 每轮仍垫最初风格参考]
  F --> G
```

---

### `/pmem-merge-ladder` — 合成梯

```mermaid
flowchart TD
  A[3 稿定升级链和画风] --> B[六条说通且 relation-judge exit 0]
  B --> C[每一档单独一张正方形]
  C --> D[像素对上才进第二段]
  D --> E[medium 抬质感 · 最多 4 轮]
  E --> F{关系还在且 ≥9.6}
  F -->|是| G[交付八张正方形]
  F -->|关系散了| H[不算过，回到过关稿改质感]
```

同框 16:9 只作体量预览，切坏了就作废，不能当成品。机读数字过了、八件合成说不通，或者画风还没写成一句，仍然不算定稿，也不能出图。这一段固定 3 稿，不再拉到 8 稿。

---

### 镜头包（写在 `/pmem-draw` 里）— 生图前点选

```mermaid
flowchart LR
  A[读参考图] --> B[短 debrief]
  B --> C[提案 4 套镜头包]
  C --> D[用户点选]
  D --> E[写入 goal / recompose_dir]
  E --> F{是否立刻 converge?}
```

本步**不出图**；批量脚本已写明构图时不要弹窗打断。

---

### `/pmem-style-lock`

```mermaid
flowchart LR
  A[丢入 1～3 张样张] --> B[提 HEX / 光影 / 笔触 / 禁用词]
  B --> C[feedback → decision + 红线]
  C --> D[输出风格锁定卡片]
```

---

### `/pmem-critique`

```mermaid
flowchart LR
  A[search + classify] --> B[五维挑刺]
  B --> C{<9.6 或用户认可?}
  C -->|是| D[feedback 写红线]
  C -->|否| E[只给审稿卡]
  D --> E
```

只审不出图。

---

### 变体（写在 `/pmem-draw` 里）

```mermaid
flowchart LR
  A[读父模块锚点] --> B[定子模块规格]
  B --> C[按 ≥9.6 收敛生图]
  C --> D[ingest 独立归档]
```

换画风 / 表情差分，不崩人设核心。

---

### `/pmem-atlas`

```mermaid
flowchart LR
  A[classify-watch 扫散图] --> B[list 模块总览]
  B --> C[atlas → art-atlas.html]
```

---

### 进阶 peek：`improve` / `coach` / `learn`

```mermaid
flowchart TD
  F[日常 converge finish] --> S[静默：反思 / taste / 红线 / learn 入队]
  S --> P{用户主动喊?}
  P -->|/pmem-coach 说进步| I[大声读进步曲线]
  P -->|/pmem-coach| C[短板 → 练习计划]
  P -->|/pmem-coach 说知识| L[列出建议 → accept 写 knowledge]
```

---

### 怎么选（30 秒）

| 你想… | 用 |
| :--- | :--- |
| 没点名具体技能，直接说 | `/pmem-agent`。定稳需求后写明交给哪一支（整页对比可依次多支） |
| 只要几套提示词，先不生图 | `/pmem-prompt` |
| 随便画一张并打磨到过线 | `/pmem-draw` |
| 主视觉 / 气氛图 | `/pmem-draw`，句子里写「原画」 |
| 一整套菜单 / HUD | `/pmem-ui` |
| App 图标 / SVG / 道具图标 | `/pmem-icon` |
| 照着某张图的风画新题材 | `/pmem-draw`，说「按这个风格画别的」 |
| 同域升级八件 | `/pmem-merge-ladder` |
| 先挑镜头再画 | `/pmem-draw`，说「先给几套机位」。点选前不生图 |
| 把样张锁成项目标准 | `/pmem-style-lock` |
| 只打分挑刺 | `/pmem-critique` |
| Q 版 / 水彩 / 表情差分 | `/pmem-draw`，说「换成 Q 版」或「做个表情差分」 |
| 整理散图看图谱 | `/pmem-atlas` |
| 看进步 / 练什么 / 学什么 | `/pmem-coach` |

---

## 第二章：王牌技能 `/pmem-draw`（4轮9.6分自评收敛生图 & 垫图生图）

平时让 AI 生图最大的痛点是：**生 1 张经常有硬伤（手崩、比例不对、混进赛博紫、漏画配饰），每次都要人工催它改。**  
`/pmem-draw` 把「生图 → 审图打分 → 挑出不合理处 → 叠加修正再生图」做成了 **全自动收敛循环**。

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

### 2.3 收敛规则与 5 项安全护栏（最多 4 次生图）
- **达到 `>= 9.6` 分（且未触发解剖 `< 7.5` 熔断）**：立即停止循环，当前图即为最终合格图（`high` / `recompose` 至少跑满 2 轮）。
- **每轮垫最初参考图**：`low` / `medium` / `high` / `recompose` 每一轮都垫最初的 `style_ref`，把上一轮具体改点追加进提示词，不改垫成图。风格跳跃不垫旧风格图，也不垫上一轮成图。`pad=previous` 仍是显式链式覆盖。
- **解剖 `< 7.5` 一票否决（熔断）**：全局停机仍以加权总分 `>= 9.6` 为准，仅当 `透视与解剖 < 7.5`（严重肢体/结构崩坏）时一票否决禁止停机；批量看板同时展示 `总分≥9.6` 与 `总分≥9.6 且 解剖≥8.5` 双指标。
- **前 3 轮不因掉分停**：生图上限就是第 4 轮。到第 4 轮时，若连续 2 轮比历史最高分低超过 `0.5`，交历史最高分那张。
- **按题材触发 R1 结构底线 + 精简回流**：仅人物/生物自动注入关节/握持/双瞳高光底线，纯空镜仅注入透视灭点与接触阴影，UI/图标跳过人体解剖词；单轮 `【回流修正】` 最多 `<= 2` 条；评分偶发失败自动重试，绝不写入泛化套话污染下一轮 Prompt。
- **满 4 次仍未达到 `9.6` 分**：停止循环，**从 1～4 轮里挑出综合评分最高且结构未熔断的那一张**作为最终结果，并说明残余不足。

### 2.4 结算、评分履历与记忆沉淀
默认对你展示：**每轮五维分 + 不足 + 改点**，以及结算时的**全轮评分履历** + 胜出图。`converge finish` 同时写出过程板 `.memory-art/converge/boards/<会话>/index.html`：参考图分析、每一轮的图和五维总分、这一轮改了什么、还差什么。一次交来多张图时，板上按图1、图2分开列，一张不丢；分析写在这些图的上方。点图片看大图，红框是胜出轮，页尾是总结。总控定需求的那几轮、合成梯的关系论述，用 `converge discuss` 记下后，也出现在这张板上。系统在后台把配方写入 `recipe`、踩坑写入 `style_redline`（不旁白记忆写入）。
报告最底部会附 **本局档位合同**：五维锁定%**不是写死的**——你一句话可微调，表上显示有效%相对本档默认的 **-xx% / +yy%**（例：low 下「构图松一点」→ **75%（默认95%，-20%）**）。也可写「光影锁定降到 40%」。裁判打分加权%只作小字备注。
- 只要终稿、不要履历：`converge finish --quiet`，或说「只要终稿」。过程板路径仍会给出。
- 不想写记忆：`converge finish --no-apply`。

---

## 第二章附：界面、原画锁定、图标

原画写在 `/pmem-draw` 的句子里，例如「原画」。界面和图标仍各读自己的技能文件，不在 draw 里生。

### `/pmem-ui`
- **怎么用**
  - `/pmem-ui 生成一套青瓷幻想风主菜单：九宫格面板 + 按钮 normal/pressed`
  - `/pmem-ui [拖入概念图] 拆出主面板九宫格、按钮四态、进度条空/满`
- **原理**：`search` 召回 UI 红线 → **概念先行**（禁止散生硬拼）→ 透明组件表 → 九宫格+状态族+`manifest.json` → **强制 4轮 ≥9.6** 收敛写记忆。

### 原画 — 写在 `/pmem-draw` 里【强制 4轮 ≥9.6】
- **怎么用**
  - `/pmem-draw 原画：东方青瓷废土主视觉 Key Art，宽幅海报`
  - `/pmem-draw [拖入参考图] 原画：同氛围角色登场 Key Art`
- **原理**：与 `/pmem-draw` **同等强制闭环**（禁止只生一张）→ 召回记忆 → FLUX 完整句 Prompt（主体靠前、排斥项正向写）→ 可选垫图解构 → `converge`（每轮展示评分履历）→ 写 `recipe`/`style_redline`（只要终稿加 `--quiet`）。

### `/pmem-icon` — 内部三模式分节隔离
- **怎么用**
  - **Mode A（1024×1024 App Icon 母版）**：`/pmem-icon 生成 1024×1024 iOS/Android 应用图标母版，中心符号占 62%–72%，带小字号缩略可读性检查`
  - **Mode B（24px `currentColor` 一致化 SVG 矢量图标集）**：`/pmem-icon 做一套 24px Clean 导航+背包 SVG，输出 style-spec 与 preview.html`
  - **Mode C（64/128/256px 游戏透明底道具栅格图标）**：`/pmem-icon 生成一套 RPG 药水与宝箱透明底道具图标，双层外描边 + 剪影秒认`
- **原理**：在 Step 0 先判定 Mode A / Mode B / Mode C 三选一（严禁把 SVG 网格规则套在栅格图标上，也严禁把 iOS 圆角遮罩套在透明底道具上）→ 关键枚 **强制 4轮 ≥9.6** → 写记忆。

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
| `python3 pmem_art.py skills --install` | 安装/刷新 `.cursor`、`.claude`、`.agents` 下的 10 个技能。每个技能一个 `/pmem-` 命令 |
| `python3 pmem_art.py skills --list` | 查看所有内置技能列表 |
| `python3 pmem_art.py converge start -g "<目标>" -m <模块> [--scale medium] [--ref-image <图> --ref-analysis "<解构>"]` | 开启一轮最多 4 次、`>=9.6` 分的收敛生图会话 |
| `python3 pmem_art.py converge generate --round <i> -i <图> -p "<Prompt>"` | **仅生图登记**（禁止带 score/dims；与 judge 必须分两步） |
| `python3 pmem_art.py converge judge --round <i> -i <图> --dims "..." --strengths "..." --defects "..." --next-fix "..."` | **独立审图**：五维打分、亮点、不合理处与下一轮修正（须先有 generate） |
| `python3 pmem_art.py converge discuss --round <稿次> -p "<正文>" --defects "<没过的行>" --next-fix "<下一稿只改哪里>"` | 记下还没出图的论述稿（合成梯关系讨论）。结算时列进过程板 |
| `python3 pmem_art.py converge finish` | 结算达标图或 4 轮最高分图；**默认写入记忆、打印评分履历，并写出可点开的过程板**（`--no-apply` 可跳过写记忆；`--quiet` 只要一行结论，过程板路径仍给出） |
| `python3 pmem_art.py feedback "<原话>" -m <模块> [-a <图>]` | 把画师自然语言评价沉淀为记忆 |
| `python3 pmem_art.py search -m <模块>` | 召回该模块（含父模块）的红线、定稿与色板 |
| `python3 pmem_art.py ingest <图> -p "<说明>" --apply` | 四信号分类并归档图片 |
| `python3 pmem_art.py atlas` | 可选：编译生成 `art-atlas.html` 可视化图谱 |

---

## 第七章：常见问题 FAQ

**Q1：如果 4 轮都没有达到 9.6 分怎么办？**  
A：到了第 4 轮仍未达 9.6 分时，`converge finish` 会自动停止循环，从 1~4 轮里挑出**综合评分最高**的那一张作为阶段最优交付图；默认给你全轮评分履历（不足/改点）+ 胜出图，并写出过程板，红框标在胜出轮上，总结里写明未到 9.60。只要终稿时加 `--quiet`，过程板路径仍会给出。

**Q2：丢入一张图让 `/pmem-draw` 生成时，它会怎么处理那张图？**  
A：它会先做 **Step 0 参考图深度解构**（分析构图、提取主辅色 HEX、判断光影与笔触、识别头身结构），把解构结论记入收敛会话基准，然后带着这份基准进入 1~4 轮自评收敛循环。

**Q3：以后升级了 `pmem-art`，怎么刷新已安装项目的技能文件？**  
A：在项目根目录运行 `python3 pmem_art.py skills --install` 即可一键无损刷新 `.cursor`、`.claude`、`.agents` 下的全部技能定义。

**Q4：没点名技能，直接说「画一张」会怎样？**  
A：走 `/pmem-agent`。固定 2 轮：第 1 轮写出需求（可默认项直接默认进定稿），第 2 轮查合理性、缺漏和理解错误。没有硬不确定、且话和图对得上，才交给现有技能执行（单交付一支；整页对比可依次多支），并回显「按 XX 走了」。硬歧义才打回问你，这一轮不生图。点名了界面、图标、合成梯、原画、克隆、变体或镜头包，就跳过总控。


---

## v0.11 连续自我迭代（能力 + 广度）

```bash
python3 pmem_art.py converge start -g "…" -m <模块>          # Warm-Start
python3 pmem_art.py converge start -g "…" -m <模块> --mode fast
python3 pmem_art.py improve run && python3 pmem_art.py progress
python3 pmem_art.py coach
python3 pmem_art.py learn suggest && python3 pmem_art.py learn accept --all
```

闭环（v0.13 履历可见）：`warm-start → 生图最多 4 轮、≥9.6（每轮展示评分/不足/改点）→ finish 打印履历 + 记忆静默自动驾驶 → 最多一行小提示 → 越用越好`。合成梯的关系讨论是 3 稿，用来定升级链和画风。只要终稿用 `--quiet`；`improve/coach/learn/progress` 为进阶 peek。

---

<a id="附录-a四档---scale-细则与示例"></a>

## 附录 A：四档 `--scale` 细则与示例

> **首页已有闸门总表**：[README · 四档闸门](README.md#四档闸门每档允许变什么--禁止变什么)。本附录补「怎么自己调」与 CLI。

两大驱动：

1. **模型自动分析收敛**：`low` / `medium` / `high` — 自主诊断缺陷、生成 `next_fix`，加权分 **`>= 9.60` 即停**。  
2. **玩家定向改构图**：`recompose` + `--recompose-dir` — 按你指定的新机位/布局改，仍锁画风与身份。

### A.1 闸门字段（与源码一致）

源文件：`skills_kit/prompt_scale.py` → `CONVERGE_SCALE_PROFILES`。

| 档位 | 提示词改动 | 最早停 | 锁住 | 可以变 |
| :--- | :--- | :---: | :--- | :--- |
| `low` | ≤20%（跟第 1 轮比） | 1 | 机位、姿态、主体数量、布局、画风色板、身份 | 局部瑕疵和局部质感 |
| `medium` | ≤40%（跟上一轮比） | 1 | 机位、主体数量、画风色板、身份。不能整张换构图 | 小幅姿态、局部布局、光影和材质 |
| `high` | ≤80%（跟上一轮比） | **2** | 画风媒介、身份。不能换成另一个主体 | 机位、姿态、布局、主体数量、戏剧光影、风格里的小叙事 |
| `recompose` | ≤85%（跟上一轮比） | **2** | 画风色板、身份、`--recompose-dir` 那句方向 | 机位和布局按这句改。姿态和光影可以跟着动。不增删主体 |

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
/pmem-draw --scale high @comparison/web_refs/web_ref_01_concept_ishtar.png 原画：升级丁达尔神光；锁身份与画风
/pmem-draw --scale recompose --recompose-dir "改为天台远眺海港全景" @comparison/style_refs/style_ref_02_pastel_sketch.png
```

生图与审图必须分两步（Skill 会自动跑）：

```bash
python3 pmem_art.py converge generate --id <sid> --round 1 -i out.jpg -p "<prompt>"
python3 pmem_art.py converge judge    --id <sid> --round 1 -i out.jpg --dims "构图9.2/光影9.1/透视9.0/质感9.0/风格9.2" --defects "..." --next-fix "..."
python3 pmem_art.py converge finish   --id <sid>   # 默认写记忆、打印评分履历，并写出过程板；只要终稿加 --quiet
```

---

## 附录 B：V4 冷启动验收摘要

来源：[docs/showcase/pmem_art_images_v4_20bots_showcase.html](docs/showcase/pmem_art_images_v4_20bots_showcase.html)

- **规模**：4 案例 × 5 档（含 `recompose_bold` 大改）= **20** Bot  
- **条件**：每 Bot 独立空目录、项目私有记忆 = 0、三步分离、画幅/垫图继承校验  
- **结果**：**20 / 20** 达到 `≥ 9.60` 停机  
- **首页图墙 + 分数进度**：见 [README.md §效果长什么样](README.md)（原图与五档终稿、R1→终分轨迹直接嵌在 README）
- 逐张 MD5 / 长文视觉核验仍以该 HTML 为准。
