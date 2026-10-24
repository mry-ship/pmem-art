# 📘 pmem-art 画师使用手册 — 怎么在 Cursor / Codex 里越画越准

> **版本**：`v0.10.0`  
> **核心理念**：日常入口就是 **Cursor / Claude Code / Codex 对话框**（外加开箱即用的 `/pmem-draw` 等 8 个斜杠技能（含垂直生成））。不用背 CLI、不用手写 YAML、不用把时间花在填表上。

---

## 目录

1. [第一章：初始化即自动安装的 8 大美术技能](#第一章初始化即自动安装的-5-大美术技能)
2. [第二章：王牌技能 `/pmem-draw`（8轮9.5分自评收敛生图 & 垫图生图）](#第二章王牌技能-pmem-draw8轮95分自评收敛生图--垫图生图)
3. [第三章：日常对话反馈怎么变成长期记忆](#第三章日常对话反馈怎么变成长期记忆)
4. [第四章：三种项目接入方式（空项目 / 老项目 / 持续生图）](#第四章三种项目接入方式空项目--老项目--持续生图)
5. [第五章：后台自动分类与多画风分叉（水彩 / Q版 / 像素）](#第五章后台自动分类与多画风分叉水彩--q版--像素)
6. [第六章：命令与收敛追踪器参考](#第六章命令与收敛追踪器参考)
7. [第七章：常见问题 FAQ](#第七章常见问题-faq)

---

## 第一章：初始化即自动安装的 8 大美术技能

当你运行 `python3 pmem_art.py init`（或 `python3 pmem_art.py skills --install`）时，系统会自动在项目根目录生成：

- **Cursor**：`.cursor/skills/<技能名>/SKILL.md` 与 `.cursor/commands/<技能名>.md`
- **Claude Code**：`.claude/skills/<技能名>/SKILL.md`、`.claude/commands/<技能名>.md` 与 `CLAUDE.md`
- **Codex**：`.agents/skills/<技能名>/SKILL.md` 与 `AGENTS.md`

你在对话框里敲 `/` 就能直接唤出：

| 主技能指令 | 简短别名 | 什么时候用 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | 想让 AI **自己反复打磨到 9.5 分以上**再交稿（支持纯文字或丢一张参考图） |
| **`/pmem-ui`** | **`/art-ui`** | 要 **一整套 HUD/菜单 UI Kit**（概念→组件表→九宫格→按钮多状态），对标 SpriteCook |
| **`/pmem-concept`** | **`/art-concept`** | 要 **原画 / 主视觉 / Key Art**：**强制 8轮 ≥9.5 收敛**（与 draw 同等，禁止只生一张）+ FLUX 完整句 Prompt |
| **`/pmem-icon`** | **`/art-icon`** | 要 **一整套风格统一的 SVG/图标**，先锁 style-spec 再分批生成（对标 jezweb） |
| **`/pmem-style-lock`** | **`/art-style`** | 拿到一张特别对味的样张，想把它的色板、光影、笔触锁成长期标准 |
| **`/pmem-critique`** | **`/art-check`** | 手头有一张图，想让 AI 对照历史红线严苛挑刺打分，并把毛病记入红线 |
| **`/pmem-variant`** | **`/art-variant`** | 角色立绘定了，想衍生 **水彩概念图 / Q版贴纸 / 表情差分 / 序列帧** 且不崩人设 |
| **`/pmem-atlas`** | **`/art-map`** | 阶段性整理散图，并刷新 `art-atlas.html` 画廊回看 |

---

## 第二章：王牌技能 `/pmem-draw`（8轮9.5分自评收敛生图 & 垫图生图）

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

### 2.2 五维严苛打分标准（满分 10.0 分，`>= 9.5` 才算合格）

每生成 1 张图，Agent 都会按五维自评并说出具体不合理的地方：
1. **风格与色板契合度（2.5 分）**
2. **构图、透视与结构合理性（2.5 分）**
3. **光影、材质与细节完成度（2.0 分）**
4. **历史红线与管线规格合规度（1.5 分）**
5. **提示词意图 / 参考图神韵还原度（1.5 分）**

### 2.3 收敛规则（最多 8 次生图）
- **达到 `>= 9.5` 分**：立即停止循环，当前图即为最终合格图。
- **未达到 `9.5` 分（且轮次 `< 8`）**：不算合格！把本轮分析出的「不合理之处」叠加进下一轮修正指令，继续生图。
- **满 8 次仍未达到 `9.5` 分**：停止循环，**从全部 8 轮中挑出分数最高的那一张**作为最终结果，并说明残余不足。

### 2.4 最终必出的全轮次评分表与记忆沉淀
无论第几轮结束，最终都会给你列出一张清晰的汇总表：
- 每一轮的 **图片路径、综合评分（含五维明细）、亮眼合理处、不合理缺陷分析、叠加修正策略、是否胜出**；
- 自动把胜出图的配方写入 `.memory-art` 的 `recipe`，把中途踩到的典型不合理项写入 `style_redline`，下次生同类图直接避坑！

---

## 第二章附：三大垂直生成技能速查

### `/pmem-ui`（`/art-ui`）— SpriteCook 式 UI Kit
1. 概念先行（整屏统一画风，可先 8轮收敛）→ 2. 以概念为垫图抽透明组件表 → 3. 标九宫格 + normal/pressed 等状态 → 4. 输出 `manifest.json` + `elements/` → 5. 关键件不够 9.5 再局部 `converge`。

### `/pmem-concept`（`/art-concept`）— 原画 / 概念图 / Key Art【强制 8轮 ≥9.5】
与 `/pmem-draw` **同一套强制闭环**：最多 8 轮、合格线 `≥ 9.5`、未达标叠加修正、满 8 轮挑最高分、输出评分总表。  
Prompt 用完整自然语言句（主体与动作靠前；排斥项写成正向描述）。CLI：`converge start → round × N → finish --apply`。

### `/pmem-icon`（`/art-icon`）— jezweb 式一致化图标集
先确认预设（Clean/Sharp/Soft/Minimal/Bold）写入 `icons/style-spec.json`，再约 5 个一批生成 SVG（统一 viewBox/`currentColor`/stroke），交付 `preview.html`；单枚可收敛。

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
| `python3 pmem_art.py skills --install` | 安装/刷新 `.cursor`、`.claude`、`.agents` 下的 5 大技能与斜杠命令 |
| `python3 pmem_art.py skills --list` | 查看所有内置技能列表 |
| `python3 pmem_art.py converge start -g "<目标>" -m <模块> [--ref-image <图> --ref-analysis "<解构>"]` | 开启一轮最多 8 次、`>=9.5` 分的收敛生图会话 |
| `python3 pmem_art.py converge round --round <i> -i <图> -s <分> --strengths "..." --defects "..." --next-fix "..."` | 记录第 $i$ 轮自评分数、亮点、不合理处与叠加修正策略 |
| `python3 pmem_art.py converge finish --apply` | 结算达标图或 8 轮最高分图，输出 Markdown 评分总表并自动写记忆 |
| `python3 pmem_art.py feedback "<原话>" -m <模块> [-a <图>]` | 把画师自然语言评价沉淀为记忆 |
| `python3 pmem_art.py search -m <模块>` | 召回该模块（含父模块）的红线、定稿与色板 |
| `python3 pmem_art.py ingest <图> -p "<说明>" --apply` | 四信号分类并归档图片 |
| `python3 pmem_art.py atlas` | 可选：编译生成 `art-atlas.html` 可视化图谱 |

---

## 第七章：常见问题 FAQ

**Q1：如果连生 8 张图都没有达到 9.5 分怎么办？**  
A：到了第 8 轮仍未达 9.5 分时，`converge finish` 会自动停止循环，从 1~8 轮里挑出**综合评分最高**的那一张作为阶段最优交付图，并在最终汇总表里完整列出每一轮的分数、亮点与剩余不足。

**Q2：丢入一张图让 `/pmem-draw` 生成时，它会怎么处理那张图？**  
A：它会先做 **Step 0 参考图深度解构**（分析构图、提取主辅色 HEX、判断光影与笔触、识别头身结构），把解构结论记入收敛会话基准，然后带着这份基准进入 1~8 轮自评收敛循环。

**Q3：以后升级了 `pmem-art`，怎么刷新已安装项目的技能文件？**  
A：在项目根目录运行 `python3 pmem_art.py skills --install` 即可一键无损刷新 `.cursor`、`.claude`、`.agents` 下的全部技能定义。
