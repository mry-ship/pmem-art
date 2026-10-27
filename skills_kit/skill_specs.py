"""Skill markdown specs for Cursor / Claude / Codex install."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from ._time import _now_cst

SKILL_SPECS: list[dict[str, Any]] = [
    {
        "name": "pmem-draw",
        "title": "【强制4轮≥9.6收敛】生图总入口：先认类型再进对应合同",
        "description": (
            "玩家要生图时使用。玩家点名了原画、克隆、变体、镜头包、界面、图标或合成梯就听玩家的；"
            "没点名则看这句话和附图自己认，认完直接做，不问选哪条技能。"
            "普通图、原画、克隆、变体、镜头包在本技能里做。整套 UI、图标集、合成梯读对应技能再做，禁止用单张插画合同代替。"
        ),
        "body": r"""# `/pmem-draw` — 生图总入口

玩家点名了类型就听玩家的。没点名就看这句话和附图自己认，认完直接往下做，中间不再让人选技能。先回显一句，例如「按原画走了」。这句只供改口，不等确认。

## 零、先认类型（一次只走一支）

玩家这句话里点了类型，就按点名走，不要改判。

| 认成 | 什么时候 | 接着做什么 |
| :--- | :--- | :--- |
| **界面** | 玩家要整屏、HUD、弹窗套件、九宫格、按钮状态 | **不要在本文件生图**。先读 `.cursor/skills/pmem-ui/SKILL.md`，只执行那一份 |
| **图标** | 桌面图标、一套线性 SVG、背包道具格 | **不要在本文件生图**。先读 `.cursor/skills/pmem-icon/SKILL.md`。A/B/C 不混用 |
| **合成梯** | 同一套东西一档比一档更大，L1–L8 | **不要在本文件生图**。先读 `.cursor/skills/pmem-merge-ladder/SKILL.md` |
| **镜头包** | 玩家明确要几套机位 / 镜头 / 光给自己挑 | 只做文末「合同 · 镜头包」，然后停。点选前禁止生图 |
| **克隆** | 有参考，并且要换一个新题材，锁的是画风 | 只做文末「合同 · 克隆」 |
| **变体** | 已有角色要换画风，或做表情 / 动作差分 | 只做文末「合同 · 变体」 |
| **原画** | 主视觉、Key Art、气氛图、概念海报 | 用下面的 4 轮闭环，提示词再守文末「合同 · 原画」 |
| **普通图** | 以上都不是 | 用下面的 4 轮闭环 |

认不准时按这个顺序收紧，不要猜成更重的合同：

1. 没人要「几套镜头」→ 不进镜头包。有参考图本身不是镜头包。
2. 有参考，但没说新题材、新物件、新角色 → **普通图**，不进克隆。
3. 单张弹框、只要一张图标 → 不升成整套界面或图标集。整套才去界面 / 图标。有参考又要换题材的这一张，走克隆。
4. 只说「画这个角色」→ 普通图或原画，不进变体。变体要出现换画风、表情或动作。
5. 回显的类型必须和实际执行的合同是同一个。玩家下一句改口，丢掉这一支重来；已经画完的图不能拿去冒充新合同的结果。

普通图和原画走第一节到第三节。克隆和变体仍用第二节的打分轮次和 `converge` 命令，但不要按第一节继承构图。镜头包、界面、图标、合成梯不要从第一节往下生。

你现在运行在 **pmem-art 闭环自评收敛生图模式**。进入普通图或原画后，**绝不能只生一张图就草草交差**（除非第 1 轮真实严苛评分就达到 `>= 9.6`）。

---

## 一、支持两种触发方式

只服务**普通图**和**原画**。类型已经是克隆、变体、镜头包、界面、图标或合成梯时，跳过这一节。

### 方式 A：纯文本指令生图
> 例：`/pmem-draw 生成一张东方青瓷水彩风格的阿斯特拉半身立绘`
- 直接进入 **Step 1（召回记忆）→ Step 2（最多4轮自评收敛循环）→ Step 3（展示评分履历 + 静默沉淀记忆）**。

### 方式 B：丢入一张参考图 / 垫图 + 生成指令
> 例：`/pmem-draw [附带一张图] 只修手指和接触阴影，机位和人物不要动`
- **必须先执行 Step 0（参考图深度解构）**：
  1. 仔细观察用户丢过来的图片（必要时用 Read 查看图像或运行 `python3 pmem_art.py classify <参考图路径>` 获取物理特征）。
  2. 输出 **【参考图视觉解构报告】**：
     - **构图与视角**：镜头景别、透视角度、主体占比、重心位置
     - **色板与光影**：提取 3~5 个主辅色 HEX、主光源方向、明暗交界线冷暖关系
     - **笔触与材质**：线条粗细/软硬、厚涂/赛璐珞/水彩颗粒感、边缘处理
     - **比例与结构特征**：头身比、关键视觉锚点、哪些亮点必须继承、哪些瑕疵不要继承
  3. 将上述解构结论写入收敛会话（`python3 pmem_art.py converge start --goal "..." --ref-image "<路径>" --ref-analysis "<解构摘要>"`），再进入 Step 1 & Step 2。

---

## 二、标准执行流程（Step 1 ~ Step 3）

### Step 1：Warm-Start 召回 & 初始化收敛会话（首轮就要接近 9 分）
1. 识别目标模块，运行 search（仍可用）：
   ```bash
   python3 pmem_art.py search --module <目标模块>
   ```
2. **启动收敛（自动注入 Warm-Start 包：Top recipes + 红线 + 个人口味）**：
   ```bash
   python3 pmem_art.py converge start --goal "<用户目标描述>" --module <目标模块> [--mode quality|fast] [--scale low|medium|high|recompose] [--recompose-dir "<新构图方向>"] [--ref-image <参考图>] [--ref-analysis "<参考图分析>"]
   ```
   - 默认 `--mode quality` = 完整 4 轮、合格线 ≥9.6。
   - `--scale`：`low` 贴原修瑕 · `medium` 小优化锁机位（默认）· `high` 大胆跃升+可叙事 · `recompose` 须配 `--recompose-dir`。
   - `--mode fast`：warm-start 置信度高时可走 **fast track**（仍须每张打分；最终采纳默认仍要 ≥9.6，除非用户明确说「草稿/fast/先看看」）。
   - 把打印出的 **Warm-Start `prompt_block` 完整并入第 1 轮 Prompt**。
   - **档位保留集（V4 短骨架；禁止全档复读肯定锁）**：
     - `low`：姿态/机位锁 **一条即可**；goal ≤20% 修瑕。
     - `medium`：goal **~40%**；锁机位；可小幅姿态/局部布局；骨架「保画风与机位，小幅姿态/局部布局；柔化光影…」。
     - `high`：goal **≤80%**；`allow_recompose` + 可改元素数；forbid=`no_identity_swap`；骨架「保媒介与身份，提升光影张力；可加风格内叙事点缀」；**≥2 轮才停**。
     - `recompose`：目标机位 = `--recompose-dir`；骨架「保画风色板，按「方向」重构机位」；**≥2 轮**；未换机位勿停；与 bold 拆开。
   - **最优方向按档分流**（加法，不是第二份锁）。出图前可跑：`python3 pmem_art.py check-scale-gates --self-check`。
   - **不要中途改去镜头包**。玩家没要几套机位，就按当前这一支继续。`high` / `recompose` 缺一句机位时，用玩家已经写的目标或档位骨架，不要停下来提议 4 套镜头。
3. **可选 Best-of-N 首帧**：第 1 轮先构思 2~3 个方向（或并行想法），挑最佳进入后续 converge（在回复里写明选了哪条）。

---

### Step 2：闭环自评收敛循环（最多 4 轮，合格线 `>= 9.6 / 10.0`）

令轮次 $i = 1, 2, \dots, 4$：

#### 2.1 生成第 $i$ 轮单张候选图
- 综合「用户原始需求 + 参考图解构特征（若有）+ `.memory-art` 历史红线 + **针对上一轮最低分维度的具体修正指令（≤2 条）**」，构造第 $i$ 轮生图 Prompt。
- **首轮（R1）按主体分类注入结构底线（认不出就不注入，禁止默认塞山体/建筑）**。词表中英两套都用来认主体；写入生图提示词的是英文，中文只在回显里给你看：
  - **人物**：关节、握持、双眼；
  - **动物**：按物种连接肢体，禁止改成人类双肘；
  - **机械体**（机甲 / 机器人 / mecha）：机械关节与接缝，不写人类瞳孔；
  - **`character.*` 但没写物种**：只写主体轮廓连续，不套人类关节；
  - **纯场景**：只写灭点与接触阴影；
  - **任务型 UI**（模块 `ui.` / `icon.`、HUD、UI kit、九宫格、图标集）不注入。button / menu / icon / 界面 / 按钮 / 菜单单独出现才算 UI；和人物、动物或场景写在一句里时跟主体走。
  - 「画一张漂亮的图」这类认不出的 brief：**不注入**。
- **垫图（每轮原图，修正只进提示词）**：
  - `low` / `medium` / `high` / `recompose`：每一轮都垫最初的参考图 `style_ref`。上一轮的具体改点追加进提示词，**不要**改垫上一轮成图或历史最高分图。
  - 没有参考图的纯文本任务：不垫成图，只在提示词上追加改点。
  - **风格跳跃（`recompose_bold` / `style_jump`）**：不垫旧风格参考，也不垫上一轮成图。剪影和画幅留在提示词里。
- 调用生图工具（如 `GenerateImage` 或项目配置的生图脚本）**生成 1 张图**。

#### 2.2 严苛审图与五维打分（每维满分 10，再按档位权重合成）
生成后亲自看图，按这五项打分（有结构、透视、质感硬伤就必须压到 9 以下）：
1. **构图** 2. **光影色彩** 3. **透视与解剖** 4. **质感** 5. **规格与风格**

示例：`构图8.6/光影8.2/透视7.8/质感8.0/风格8.4`。旧的加和尺 `风格2.2/结构2.0/光影1.7/合规1.4/还原1.3` 仍可解析为相加总分。

#### 2.3 记录到收敛器（生图和审图必须分两步）
```bash
python3 pmem_art.py converge generate \
  --session <id> --round <i> --image "<图片路径>" --prompt "<本轮 Prompt>"
python3 pmem_art.py converge judge \
  --session <id> --round <i> --image "<图片路径>" \
  --dims "构图8.6/光影8.2/透视7.8/质感8.0/风格8.4" \
  --strengths "<亮点>" \
  --defects "<缺陷，具体到部位>" \
  --next-fix "<下一轮要改的正向描述>"
```
不要把 `--score` 当成最终分。五维解析成功后，停机分以加权结果为准。

#### 2.4 向用户展示本轮审图卡（默认必做）
在继续下一轮或进入结算前，把本轮结果写进对话（除非用户 `--quiet`）：
`第 i 轮 · 总分 X.XX · 五维… · 不足：… · 本轮/下轮改点：…`，并附上本轮图。

#### 2.5 收敛判定（核心规则！）
- **情况 1：本轮评分 `>= 9.6`、已满本档 `min_rounds_before_stop`（`high`/`recompose` 默认 ≥2 轮），且未触发解剖硬伤一票否决（`perspective_anatomy >= 7.5`）**
  🎉 **合格达标！** 结束生图循环，以第 $i$ 轮为胜出图，进入 Step 3。
  - **解剖硬伤一票否决（人物/动物 `< 7.5` 禁停；纯场景只在 `< 6.0` 禁停）**：人物或动物总分 `>= 9.6` 但 `透视与解剖 < 7.5`（肢体融化）禁止停机。纯场景这一维主要是透视，`7.5` 以下的轻微偏差允许停，只有 `< 6.0` 的结构崩坏才禁停。缺这一维仍然 fail-closed。看板另列「总分≥9.6 且解剖≥8.5」。下一轮改点若是「加强氛围 / 提升体积光」这类空话，由回流策略改成 ≤2 条部位级修正。
- **情况 1b：分数够但未满最小轮次** → 视为未停机，按 `best_direction_hint` 继续叠加（防 1 轮贴原虚高）。
- **情况 2：本轮评分 `< 9.6` 且 $i < 4$**
  🔄 **不合格！** 必须把本轮最低分维度的具体硬伤转化为 **≤2 条部位级修正指令**（如具体关节/持物连接、接触阴影、边缘描边），并入第 $i+1$ 轮 Prompt，**严禁**堆砌「加强氛围、提升体积光」等空泛套话；若本轮评分解析失败，先重试 1 次，仍失败则保持上一轮有效缺陷与底图，绝不用套话污染 Prompt。
- **情况 2b：第 4 轮过峰（第 4 轮已是上限）**
  🛑 前 3 轮允许 `high`/`recompose` 先跌后升，不因掉分停。到第 4 轮，若连续 2 轮都比历史最高分低超过 `0.5`，交付历史最高分那张。
- **情况 3：已满 4 轮（$i = 4$）且评分仍 `< 9.6`**
  🏁 **达到 4 轮上限，停止循环！** 从第 1 ~ 4 轮中**挑选综合评分最高的那一轮图片**作为最终交付图，进入 Step 3。

---

### Step 3：结算最优图 & 自动沉淀记忆（默认展示评分履历；记忆写入仍静默）

循环结束后，运行：
```bash
python3 pmem_art.py converge finish
```
该命令会自动：
1. 选出达标轮次（`>= 9.6`）或全阶段最高分轮次（`Best of 4`）。
2. 将最终胜出图通过 `ingest` / `feedback` 写入 `.memory-art` 的 `recipe`（正向定稿锚点），并把迭代过程中暴露的典型不合理点写入 `style_redline` / `visual_correction`。
3. 生成并**默认打印**标准 Markdown 评分履历，同时写出可点开的过程板 HTML（只要一行结论时加 `--quiet`，过程板路径仍给出）。

**对用户的默认展示（过程可见 · 记忆写入静默）：**
每轮 `converge judge` 之后，在对话里写本轮审图卡（用户说「安静/quiet」或 CLI `--quiet` 才可省略）：五维分、总分、不足、下一轮改点。
`converge finish` 会写出一张可点开的过程板 HTML。结算时按这个顺序给玩家：
1. **参考图分析**（有参考才写）：构图机位、色板光影、要锁的身份、不要继承的部分。
2. **每一轮出图**：图、五维、总分、这一轮相对上一轮改了什么、还差什么。
3. **过程板**：把 HTML 路径给玩家。板上每张图都能点开看大图，胜出轮有红框。论述稿和出图轮都在这一张板上。
4. **总结**：胜出哪一轮、总分、留下的那一处不足。
有多轮论述（合成梯关系稿）时，每一稿都要先记，不能只留在对话里：
```bash
python3 pmem_art.py converge discuss --round <稿次> --prompt "<这一稿正文>" --defects "<没过的行>" --next-fix "<下一稿只改哪里>"
```
报告**最底部**必须带档位合同脚注（`converge finish` 已打印），原样转述，例如：
> **目前是 LOW 档**… 若画师说「构图松一点」，表上该维显示 **`75%（默认95%，-20%）`**（档位仍是 low，只微调这一维）。
画师可写：`构图松一点` / `光影锁定降到 40%` / `升到 medium`；Agent 应跑 `converge lock --lock-text "…"` 再继续生图。
💡 若 CLI 打出一行「小提示」，原样转述（每会话最多 1 条）。
**禁止**旁白「正在写反思 / 更新 taste / 入队 learn / 沉淀红线」——记忆仍在 `finish` 后台静默完成。
improve/coach/learn 推销仅在用户主动要时再给。

### Agent 后台（对用户不可见）
`finish`（默认写记忆；`--no-apply` 可跳过） 已自动：写 recipe/红线 + 会话反思 + `run_silent_autopilot`（更新 taste、强化配方、悄悄 enqueue 1–2 条 learn 建议）。

### 闭环总览
`装上就用 → 先认类型 → 画 → 每轮摊开评分与改点 → 偶发一行小提示 → 记忆后台变强；只要终稿用 --quiet；进阶偷看用 /pmem-coach`
## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**参考图分析 + 每轮五维与总分 + 可点开的过程板 + 总结**；记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看进步、短板或知识卡时再用 `/pmem-coach`。

## 合同 · 原画

只在类型是原画时加在闭环上。闭环轮次、9.6、评分履历与上面相同。

提示词用完整句子，不要纯 tag。顺序：主体与动作，场景，光影与时段，材质与画风，色板，景别画幅。排斥项写成正向句（「干净的青瓷白与墨蓝，无霓虹」）。每轮用上一轮的具体缺陷重写整句，仍禁止只堆负向 tag。

## 合同 · 克隆

只在类型是克隆时执行。轮次用第二节的 `converge generate` / `judge` / `finish`，最多 4 轮，合格线 ≥ 9.6。不要按第一节继承参考构图。禁止无五维数字宣称通过。默认锁大约 95% 的画风，换的是题材。

- **没有参考**：只靠 brief 和自写风格圣经。媒介必须在 brief 里写明。
- **有参考**：每一轮都垫最初那张风格参考。比例、眼型、描边、文案的修正写进提示词，不要垫上一轮成图。禁止事后拿无关图当原图对照。

**锁**：媒介、色板角色、光感、材质语法、红线。按类再加：

- 场景 / 原画：锁媒介和光感，构图可以换。
- **界面弹框母版**：锁媒介和双层描边（参考有两层就把两层都锁住）。新题材是空内容的九宫格面板：中心大块留白，角区不放复杂纹样。禁止把参考里的道具（如礼盒）放进内容区。顶栏纹样最多 1 个。底栏只用符号钮。没有 brief 就不造可读界面文字。参考若是道具图标，分析里写明「只借材质描边，不借布局和主体」。整套组件仍走 `/pmem-ui`，克隆只交一张母版。内容区回声了参考主体 → 压分并且不可停。
- 图标：锁外框、材质、背景习惯。主体是新的。纹样最多 1 个。缩略轮廓要清楚。搪胶、软塑胶体积只在参考本身是玩具或 Q 版时才写。
- 角色：脸的画法跟参考媒介。通用只锁双眼分穴、虹膜、巩膜月牙、高光，禁止独眼和黑点瞳。软颊、短粗肢、大头桶身只在卡通或 Q 版参考里才写。换装可以，禁止三视图。角色身份不是名人脸或著名服装。

**不锁**：构图、题材、身份，除非玩家要求保留。尺寸按玩家说的来，否则跟参考。

风格圣经从参考像素归纳媒介、色板、描边。参考是道具图标时，禁止把道具外形写进界面 brief。界面 brief 写清空内容弹框、禁止中心纹样、符号钮。

五维仍是 `构图/光影/透视/质感/风格`。构图分同时看有没有把参考题材抄回来。构图低于 6.0，或缺陷写了抄回参考主体、礼盒进了内容区，压到 8.85 以下并且不能停。≥9.6 且结构门过了才停。主参考是黑点瞳而合同要虹膜时，写死虹膜，禁止为了贴参考改回黑点眼。

交付时对照的是这趟真正垫过的参考。

## 合同 · 变体

只在类型是变体时执行。轮次用第二节的 `converge generate` / `judge` / `finish`。先 `python3 pmem_art.py search --module <父模块>`，锁住不能改的人设：发色、瞳色、标志配饰、主色板。

- 换画风：另建子模块（如 `character.Astra.Chibi`）。不垫旧画风原图，人设只写进提示词。
- 表情或动作差分：每一轮垫最初的角色原图，修正只写进提示词。锁五官比例和机位。

然后按上面的 4 轮、≥9.6 闭环生图。完成后 `python3 pmem_art.py ingest <新图路径> -p "<含角色名和画风或差分的提示词>" --apply`。

## 合同 · 镜头包

只在类型是镜头包时执行。看参考图，给 4 套可点的机位方案，然后停。禁止在这一步生图，禁止编分数。

每套写清：机位（高度、角度、景别）、光（方向和色）、1–3 个具体道具、明确禁止项、一句可直接拿去生图的目标。至少一套接近原图机位，至少一套真的换机位。用具体名词，不要写「加强氛围」。身份和媒介留在参考上。玩家点了一套之后，再按点名进入原画、普通图或其它合同。没点选就停。
""",
    },
    {
        "name": "pmem-style-lock",
        "title": "参考图/样张一键提炼风格圣经与色板锁定",
        "description": (
            "当用户输入 /pmem-style-lock 并附带样张/参考图时触发。"
            "自动解构样张的主辅色板 HEX、光影法则、笔触特征与禁用词，一键锁定为项目或模块的风格基准（art_decision + recipe）。"
        ),
        "body": r"""# `/pmem-style-lock` — 样张提炼风格圣经与色板锁定

当用户丢入 1~3 张满意的样张或概念图，希望「以后项目/这个角色就按这个画风来」时执行：

1. **视觉基因深度提取**：
   - **主辅色板（Palette）**：提取主色（70%）、辅色（20%）、点缀色（10%）的精确 `#HEX` 值与中文命名。
   - **笔触与渲染（Rendering）**：线稿粗细与颜色、赛璐珞分层数 / 厚涂笔触感 / 水彩边缘扩散度。
   - **光影与氛围（Lighting）**：主光源角度、环境光色温、高光材质表现（金属/丝绸/青瓷/发光体）。
   - **严禁偏离项（Anti-Style Redlines）**：明确列出哪类常见 AI 坏习惯会破坏该画风（如过度霓虹、脏暗阴影、油腻高光、错误头身比）。
2. **自动写入记忆库**：
   - 调用 `python3 pmem_art.py feedback "以后统一按此样张画风：<核心色板+光影+笔触摘要>" --module <目标模块> --asset <样张路径> --kind art_decision`
   - 调用 `python3 pmem_art.py feedback "禁止偏离样张画风：<反例禁用词汇总>" --module <目标模块> --kind style_redline`
3. **输出《风格锁定卡片》**：用清晰的表格展示色板 HEX、正向风格词、负向禁用词与已写入的记忆路径。
""",
    },
    {
        "name": "pmem-critique",
        "title": "单图/批量图主美级五维审稿与红线入库",
        "description": (
            "当用户输入 /pmem-critique 对现有图片进行审稿挑刺时触发。"
            "对照项目历史红线与模块规格进行五维打分，指出不合理之处，并可将问题一键记入 style_redline。"
        ),
        "body": r"""# `/pmem-critique` — 主美级五维审稿与红线入库

当用户丢入一张或多张图让 Agent「审一下 / 看看哪里不合理 / 打个分」时执行：

1. **召回模块基准**：
   - 运行 `python3 pmem_art.py search --module <模块>` 获取已有红线、色板与管线规格。
   - 运行 `python3 pmem_art.py classify <图片路径>` 获取分辨率、宽高比、Alpha 透明通道等物理参数。
2. **五维打分与挑刺（每维 0–10 分，按档位权重合成 10.0 分）**：
   - 统一按 **`构图 / 光影 / 透视 / 质感 / 风格`** 五个维度各打 0–10 分（例：`构图8.8/光影8.5/透视7.9/质感8.4/风格8.8`），保证档位权重与 `perspective_anatomy`（透视与解剖）维度检测正常生效。
   - 明确列出 **✅ 合理亮点** 与 **❌ 不合理/需返修点**，并给出可直接用于下一轮重绘的 **修正 Prompt 建议**。
3. **自动沉淀红线**：
   - 若评分 `< 9.6` 或用户认可某条挑刺结论，调用 `python3 pmem_art.py feedback "<具体不合理点>" --module <模块> --asset <图片路径>` 自动写入记忆库。
4. **静默默认**：向用户最多一句「小提示」（如「下次注意：光影」）；完整教练报告仅当用户明确要 `/pmem-coach` 或 `--verbose`。
""",
    },
    {
        "name": "pmem-atlas",
        "title": "一键归档散图、记忆体检并刷新可视化图谱工作台",
        "description": (
            "当用户输入 /pmem-atlas 时触发。"
            "自动扫描归位未分类散图、运行管线与记忆过期体检，并重新生成 art-atlas.html。"
        ),
        "body": r"""# `/pmem-atlas` — 整理散图与刷新可视化图谱

当用户想阶段性整理项目里的生成图、查看目前积累了多少条红线与定稿配方时执行：

1. **扫描未归档新图**：
   ```bash
   python3 pmem_art.py classify-watch
   ```
   汇报有哪些散图待归档（若用户同意，加 `--apply` 自动归位）。
2. **模块与记忆总览**：
   ```bash
   python3 pmem_art.py list
   ```
3. **重新编译单文件交互式图谱**：
   ```bash
   python3 pmem_art.py atlas
   ```
   告知用户可随时双击项目根目录的 `art-atlas.html` 检视正反例滑杆与配方卡。
""",
    },

    {
        "name": "pmem-ui",
        "title": "【强制4轮≥9.6收敛】SpriteCook式 UI Kit/HUD/九宫格整套",
        "description": (
            "仅当玩家点名 UI/HUD/九宫格，或生图分流判成整套界面时使用。不要用来画普通插画、单张克隆或合成梯。"
            "概念稿与关键组件均强制「最多4轮、合格线≥9.6」闭环自评收敛（生1张→打分挑刺→展示不足与改点→<9.6叠加修正→满4轮挑最高分→评分履历可见）。"
            "流水线对标 SpriteCook：概念先行 → 透明组件表 → 九宫格切线 → 状态族。"
            "触发例：「/pmem-ui 生成一套蒸汽朋克主菜单 HUD」「/pmem-ui [附概念图] 拆出九宫格弹窗与按钮态」。"
        ),
        "body": r"""# `/pmem-ui` — SpriteCook 式 UI Kit / HUD / 九宫格整套生成

只在玩家点名界面，或 `/pmem-draw` 判成「界面」之后执行。不要用单张插画合同代替这套管线。

## 怎么用（复制即用）
```text
/pmem-ui 生成一套青瓷幻想风主菜单：九宫格面板 + 按钮 normal/pressed/disabled
/pmem-ui 做一套蒸汽朋克战斗 HUD（血条空满、技能槽），透明底
/pmem-ui [拖入概念图] 按概念拆出主面板九宫格、主按钮四态、进度条空/满、Tab 两态
```

## 原理（截图摘要）
1. `search` 召回 `ui.*` 红线与定稿 → 2. **概念先行** → 3. 透明组件表 → 4. 九宫格 + 状态族 → 5. **强制 4轮 ≥9.6**（每轮展示评分履历） → `finish` 打印履历 + **记忆静默写入**（勿旁白记忆）

你现在运行在 **pmem-art UI Kit 模式**（对标 SpriteCook UI Kit Builder：概念先行 → 组件表 → 九宫格切线 → 状态族）。**禁止**把整屏各控件零散各生一张再硬拼；必须先锁一个统一视觉语言的概念稿，再从同一概念抽出可复用零件。

---

## 一、适用场景
- 主菜单 / HUD / 暂停 / 设置 / 背包 / 对话框 / 商店 / 任务日志 / 角色面板 / 地图 / Game Over / Overlay
- 需要 **九宫格可拉伸面板、按钮多状态（normal/hover/pressed/disabled）、进度条空满态、标签选中/未选中** 的成套 UI

## 二、标准流水线（Concept → Sheets → 9-Slice → Converge）

### Step 0：确定屏幕类型与规格
确认：屏幕类型、平台（桌面/主机 vs 移动）、画幅（16:9 / 超宽 / 竖屏）、目标模块（如 `ui.MainMenu` / `ui.InventoryHUD`）。
```bash
python3 pmem_art.py search --module <ui.模块>
```

### Step 1：概念先行（Concept First）—— 不可跳过
1. 若用户丢入概念图：先做参考图视觉解构（构图分区、主辅色 HEX、金属/木纹/霓虹材质、控件密度），再进入组件抽取。
2. 若无概念图：先生成 **1 张完整屏幕概念稿**（整屏布局，统一材质与色板），用 `/pmem-draw` 同款 **4轮 >=9.6 收敛** 打磨概念稿：
   ```bash
   python3 pmem_art.py converge start --goal "UI概念稿：<屏幕类型+风格>" --module <ui.模块> [--scale medium|high]
   # 每轮：converge generate 生图，再 converge judge 审图，直到 >=9.6 或满 4 轮
   python3 pmem_art.py converge finish
   ```
3. **概念稿通过后才进入组件表**——不要在概念未锁定时散生按钮。

### Step 2：从概念抽取组件表（Component Sheets）
以概念稿为垫图/参考，在 **透明底** 上生成组件表（1~3 张 sheet），覆盖：
- **面板 / 边框 / 装饰条**（可九宫格拉伸）
- **按钮族**：至少 normal + pressed（最好含 hover / disabled）
- **进度条 / 血条**：空轨 + 满轨（或分段填充）
- **标签 / Tab**：选中 + 未选中
- **图标位 / 分隔线 / 角花** 等概念中出现或隐含的零件
同一概念参考下批量生成，保证木纹/螺栓/色板/光影角度一致。概念稿和组件表的每一轮都垫最初那张参考（用户概念图，或已定稿的概念稿），不改垫上一轮生成结果，修正只追加进提示词。缺件时只补缺件，不要整套重开。

### Step 3：九宫格切线与清单（9-Slice + Manifest）
对每个可缩放件标注九宫格：四角固定、四边单向拉伸、中心双向拉伸。输出清单建议：
```
ui_kit_<name>/
├── concept.png
├── sheets/
├── elements/          # 透明 PNG 单件
├── manifest.json      # name / group / state / rect / nine_slice {l,r,t,b}
└── preview.html       # 可选：拼装预览
```
`manifest.json` 示例字段：`name`, `group`, `state`, `file`, `nine_slice: {left,right,top,bottom}`, `scalable: true|false`。

### Step 4：关键件二次收敛（可选但推荐）
对主面板、主按钮等核心件，若五维评分 `< 9.6`（重点查：中心拉伸区是否干净、转角是否形变、透明底毛边、状态族是否同系），再跑一轮 `converge generate` 局部重绘，然后 `converge judge` 审图。

### Step 5：沉淀记忆
```bash
python3 pmem_art.py ingest <concept或主面板路径> -p "UI kit <屏幕> 概念/主面板" --apply
python3 pmem_art.py feedback "UI套件色板与九宫格规范：<摘要>" --module <ui.模块> --kind art_decision
```

## 三、UI 专用五维评分侧重（满分 10.0，`>= 9.6` 合格）
1. 风格色板契合（2.5）— 与概念稿同材质同色板
2. 结构/九宫格合理性（2.5）— 中心区干净、角不糊、可拉伸
3. 光影材质完成度（2.0）
4. 红线与管线合规（1.5）— RGBA 透明底、分辨率、无脏边
5. 套件一致性 / 状态族完整（1.5）— normal/pressed 等同系，不「各画各的」

## 四、最终交付必须包含
1. 概念稿 + 组件表 + `elements/` + `manifest.json`（含九宫格）
2. 若跑了收敛：默认附上全轮次评分优劣总表（不足/改点）；只要终稿用 `--quiet`
3. 已写入 `.memory-art` 的 recipe / redline 路径


## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
""",
    },
    {
        "name": "pmem-icon",
        "title": "【强制4轮≥9.6收敛】iOS/Android App Icon 应用图标母版 + jezweb式一致化 SVG 图标集 + 游戏道具栅格图标",
        "description": (
            "仅当玩家点名图标，或生图分流判成桌面图标、SVG 图标集、游戏道具格时使用。A/B/C 不混用。不要用来画普通插画或合成梯。"
            "(A) iOS/Android 1024×1024 App Icon 桌面启动图标母版（满幅直角出图+72%~80%圆角安全区+多尺寸导出矩阵+深浅色自适应）；"
            "(B) jezweb 式一致化 SVG 矢量图标集；(C) 游戏道具 64/128/256px 透明底栅格图标。"
            "全部支持 converge generate 与 converge judge 两步分离，以及动态阈值收敛闭环。"
        ),
        "body": r"""# `/pmem-icon` — jezweb 式一致化图标集 / SVG 取向生成

只在玩家点名图标，或 `/pmem-draw` 判成「图标」之后执行。先分 A/B/C，三条不混用。单张「按这张画风换一个新道具」走 `/pmem-draw` 的克隆合同，不在这里做成一整套。

## 怎么用（复制即用）
```text
/pmem-icon 给本项目做一套 24px Clean 预设导航+背包图标（SVG），输出 style-spec 与 preview.html
/pmem-icon home settings inventory craft map quest
/pmem-icon [拖入品牌样张] 按这个线宽与圆角补齐：phone email location
```

## 原理（截图摘要）
1. 先锁 **style-spec** → 2. SVG 硬规则 → 3. 分批生成 → 4. 交付 preview → 5. 关键枚 **Warm-Start + 最多 4 轮 ≥9.6** → 6. 反思写进记忆，要看报告再用 /pmem-coach

你现在运行在 **pmem-art 图标集模式**（对标 jezweb `icon-set-generator`）：先锁 **一份 style-spec**，再批量生成，保证 stroke、圆角、视口、视觉重量一致——**禁止**从 Lucide/Heroicons 随便拼一套「看起来差不多」的通用库图标冒充项目定制集。

---

## 一、三大模式分流（入口只有 `/pmem-icon`，按需求进对应分节，严禁串味）
- **【Mode A · App Icon 1024 母版】**（手机桌面启动图标 / iOS App Store / Android Adaptive / 产品 Logo）→ 直接跳至下方 **「## 二之二、Mode A：App Icon 1024×1024 母版专项」**（满幅直角 + 72%–80% 安全区 + 微立体光影，不用 SVG 规则）。
- **【Mode B · 24px 线性 SVG 图标集】**（网页 / App 导航栏 / HUD 矢量图标）→ 执行下方 **「## 二、Mode B：一致化 SVG 矢量图标集流程」**（只用 `currentColor` + 统一 stroke/viewBox）。
- **【Mode C · 游戏道具栅格图标】**（背包 64/128/256px 透明底 PNG 道具）→ 执行下方 **「## 二之三、Mode C：游戏道具透明底栅格图标」**（锁描边/色板/投影，不用 SVG 代码）。

## 二、Mode B：一致化 SVG 矢量图标集流程（Brief → Spec → Batch → Review → Converge）

### Step 1：理解项目与图标清单
收集：行业/项目气质、品牌色（即使 SVG 用 `currentColor` 也影响线型选择）、大约数量。
按组建议清单（可让用户增删）：
- Navigation / Communication / Trust / Actions / Industry-Specific（或游戏：Inventory / Combat / Status / Crafting）

### Step 2：锁定 Style Spec（生成前必须确认）
推荐预设起步：

| Preset | 适用 | Stroke | Caps/Joins | Corners |
|--------|------|--------|------------|---------|
| Clean | 多数业务站 | 1.5px | round/round | 2px |
| Sharp | 科技/硬核 | 1.5px | square/miter | 0px |
| Soft | 亲和/休闲 | 2px | round/round | 4px |
| Minimal | 编辑/优雅 | 1px | round/round | 0px |
| Bold | 高识别/无障碍 | 2.5px | round/round | 2px |

写入 `icons/style-spec.json`（含 grid/viewBox、strokeWidth、linecap、linejoin、padding、opticalBalance、icons[]）。

### Step 3：SVG 硬规则（整套必须统一）
```xml
<svg xmlns="http://www.w3.org/2000/svg" width="{grid}" height="{grid}"
  viewBox="0 0 {grid} {grid}" fill="none" stroke="currentColor"
  stroke-width="{strokeWidth}" stroke-linecap="{…}" stroke-linejoin="{…}">
  <!-- paths -->
</svg>
```
1. **只用 `currentColor`**，禁止写死 `#000` / `blue`
2. **同一 viewBox**、同一根节点 stroke 属性
3. 无根节点 transform；无无用 id/class
4. 坐标最多 2 位小数；保持 padding；视觉居中（光学校正）
5. 路径尽量少；简单图标略加重以平衡视觉重量

### 二之三、Mode C：游戏道具透明底栅格图标（64/128/256px PNG，非 SVG）
若用户要的是 **游戏道具栅格图标**：先锁「线宽/圆角/色板/投影」style-spec，再批量生成透明底 PNG（同色板、同描边、同光源投影、中心缩略轮廓清晰、无文字），关键单枚可用 `converge` 跑 4 轮 ≥9.6 打磨。

### Step 4：分批生成（约每批 5 个）+ 一致性审查
每批完成后检查：stroke 是否漂移、圆角是否混用、有无图标明显偏轻/偏重、是否贴边。
全部完成后生成：
```
icons/
├── style-spec.json
├── preview.html      # 含 1x/2x 与深色底对比，内联 SVG
├── home.svg
└── …
```

### Step 5：关键图标 4轮9.6 收敛（可选）
用户点名某枚「不对」或一致性审查不通过时，每一轮垫最初的风格参考或 style-spec 样张，不垫上一轮成图：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module brand.WorldStyle
# 生成 → 自评 → converge generate / converge judge → finish
```

### Step 6：沉淀
```bash
python3 pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module brand.WorldStyle --kind art_decision
python3 pmem_art.py ingest icons/preview.html -p "icon set preview" --apply   # 若适用
```

## 二之二、Mode A：App Icon 1024×1024 母版专项（iOS App Store / Android Adaptive 桌面启动图标）

当用户要求制作 **App Icon / 手机桌面图标 / iOS 启动图标 / Android 自适应图标 / 产品 Logo 图标** 时，自动切换至 **App Icon 专项模式**：

### 1. 1024×1024 满幅直角母版与系统圆角安全区铁律
- **严禁预裁透明圆角**：母版必须输出 **`1024×1024` 满幅直角正方形（Full-bleed Square PNG，无 Alpha 透明缺角）**，防止系统套用 iOS 超椭圆（Superellipse Squircle）或 Android Adaptive 遮罩时露出黑边/白边裂隙。
- **核心图形安全区（Center 72%–80% Safe Zone）**：核心主符号（Hero Glyph）必须收束在画布中心 **`72%–80%`（约 `740×740 px`）安全圆/超椭圆内**，四周留出充足呼吸负空间，绝不贴边。
- **零细碎文字红线**：App Icon 严禁堆砌 Slogan、副标题或复杂多角色场景；只保留 **1 个高辨识度核心记忆符号**，确保缩放到 `29×29 px`（设置页）与 `60×60 px`（通知栏）时依然一眼认出。

### 2. 光学微立体质感与光影层次（Tactile Material & Lighting）
- **三层景深结构**：① 底板环境渐变层（70% 主色）→ ② 中心主符号微倾体块层（20% 辅色 + 柔和接触阴影 Contact Shadow）→ ③ 顶部 45° 高光切角边缘（Top-Edge Specular Rim，10% 点缀色）。
- **支持 iOS 18+ 三态适配**：输出标准浅色版（Light）、深色模式版（Dark Mode 深邃底板+自发光边缘）与单色着色版（Tinted 单通道明度层次）。

### 3. 多尺寸导出矩阵与 `app-icon-preview.html`
通过 `converge generate` 与 `converge judge` 分两步收敛出 `1024×1024` 母版后，自动导出标准尺寸包：
- **iOS 矩阵**：`1024×1024` (App Store)、`180×180` (@3x Home)、`167×167` (iPad Pro)、`120×120` (@2x)、`60×60` (Notification)、`29×29` (Settings)
- **Android / 桌面矩阵**：`512×512` (Play Store)、`192×192` (xxxhdpi Foreground/Background)

### 4. App Icon 专属五维审图标准（满分 10.0 分，支持 `parse_5d_dims` 自动加权）
1. **品牌符号与小尺寸识别度（25%）**：核心图形是否极致凝练？缩至 `29px / 60px` 轮廓是否依然清晰秒认？
2. **1024母版与圆角遮罩安全区合规（25%）**：是否为满幅直角母版？主体是否严格落在中心 `72%–80%` 安全区内、无贴边裁切？
3. **光影与微立体质感完成度（20%）**：顶部高光切角、材质折射/磨砂肌理与底部环境漫射阴影是否精致通透、无廉价塑料感？
4. **多尺寸导出与深浅色自适应合规（15%）**：Light / Dark / Tinted 三态及多尺寸缩放是否无糊边、无伪影？
5. **色板纯粹度与无细碎文字红线（15%）**：是否严格遵循 70-20-10 品牌色板？是否 100% 剔除了多余文字与杂乱背景？

```bash
python3 pmem_art.py converge start --session appicon --module brand.WorldStyle --scale high --goal "iOS 1024x1024 App Icon: 青瓷质感记账应用，中心单枚立体青釉金币流光符号"
python3 pmem_art.py converge generate --session appicon --round 1 --image app_icon_r1.png --prompt "..."
python3 pmem_art.py converge judge --session appicon --round 1 --image app_icon_r1.png \
  --dims "识别度9.6/安全区9.7/光影质感9.5/多尺寸合规9.6/色板纯粹9.7"
```

## 三、交付检查清单
- [ ] 全部 SVG 同 viewBox / stroke-width / linecap / linejoin
- [ ] 全部 `currentColor`
- [ ] 视觉重量平衡、padding 一致、光学居中
- [ ] 文件名 kebab-case；`preview.html` + `style-spec.json` 齐全
- [ ] 若跑了收敛：默认展示每轮评分/不足/改点 + 胜出图（只要终稿用 --quiet）

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
""",
    },
    {
        "name": "pmem-coach",
        "title": "【进阶/可选】进步、短板与知识卡（日常已静默写过）",
        "description": (
            "玩家要看进步、口味、短板练习或知识卡时使用。只有 /pmem-coach 这一条。"
            "日常 converge finish 已经在后台写过，不要主动推销。知识卡没有玩家明确说收下，就不要写入。"
        ),
        "body": r"""# `/pmem-coach` — 进步 / 短板 / 知识（三条偷看合成一条）

日常 `converge finish` 已经在后台写过反思、口味和知识队列。只有玩家来要报告时才跑。一次只出一份，不要把三份一起倒出来。

看玩家这句话里要哪一份。没点明就只出短板。

| 玩家在说 | 跑 |
| :--- | :--- |
| 总结、进步、口味 | 进步 |
| 知识、技法、广度 | 知识 |
| 短板、练习、练什么，或没点明 | 短板 |

## 进步
```bash
python3 pmem_art.py improve run
python3 pmem_art.py progress
python3 pmem_art.py taste show
```

## 短板
```bash
python3 pmem_art.py coach
python3 pmem_art.py progress
```
红线加会话反思，收成构图、光影、解剖、九宫格等短板，给下一张该练什么。

## 知识
```bash
python3 pmem_art.py learn suggest
python3 pmem_art.py learn list
```
只列出建议。玩家明确说「收下」或「写入」之后，才运行 `python3 pmem_art.py learn accept`。禁止自动 `accept --all`。
""",
    },
    {
        "name": "pmem-merge-ladder",
        "title": "同域合成梯：先过八件关系，再逐张抬到 ≥9.6",
        "description": (
            "玩家要一条同域合成升级梯，或生图分流判成合成梯时使用。"
            "只有 /pmem-merge-ladder：先文字定稿八件关系，再每一档单独一张正方形。"
            "同框整梯只作体量预览，不是交付物。关系讨论固定 8 稿，合成说不通就不能出图；第二段跑图最多 4 轮。"
        ),
        "body": r"""# `/pmem-merge-ladder` — 同域合成梯

一条合同。同框不是交货，交货是一档一张正方形。

交付物是八张同样大的正方形，每张只有一件、居中。16:9 八格同框只允许当体量预览；预览切格切进了邻件，整张预览作废，不能拿去当成品。

## 风格（第二段才用，只取一条）

1. 玩家写下了风格，就用写下的。
2. 没写风格但有参考图：先跑 `python3 pmem_art.py ref-read <参考图路径>`，把看见的表面写成一句。底是透明的，不要写成黑底。小高光不要写成油亮。表面光洁，不要改成毛毡或纸纹。不要把参考图文件垫进生图。不抄参考里的物件。
3. 风格和参考都没有：质感好的卡通可爱。圆润倒角、软阴影、饱和友好色，道具本身无脸，除非玩家要求有脸。没写明玩具、Q版或卡通时，生成前剥掉 vinyl、chibi、搪胶、桶身、金琥珀双描边。圆润和软阴影可以留着，不必靠这些词。

默认卡通或风格化参考下，产品实拍、油光不锈钢、真实木纹微细节要重扣。只有参考或 brief 明确写实才允许写实。

## 第一段 · 关系讨论（8 稿，先不出图）

这一段不是跑图。跑图上限是 4 轮，不能拿来缩短这里。关系要谈到严谨，最多改 **8 稿**。8 稿里没有一稿把下面六条都说通，就停在这一段，一张图都不出。

每一稿写成八行，交给独立文本判断。只谈关系，不谈画风、光影、质感。判断要指出没过的是哪一行、哪一条。没过只改那几行，已经说通的行锁住。不写「不要画某件」。

每一稿立刻记入会话。finish 的过程板按稿次列出这些论述，不能只留在对话里。第一段开始前先 `converge start`，这一段还不出图。

```bash
python3 pmem_art.py converge discuss --round <稿次> --prompt "<这一稿八行>" --defects "<没过的是哪一行>" --next-fix "<下一稿只改哪几行>"
```

六条都要过，而且要说得通：

1. 正好八件，`level` 为 1 到 8。同一任务域，不许串成同色杂物。
2. 每一档画面里将只有一件、居中。不是一对，也不是一组场景。无脸，无等级字。
3. 两件相同的这一档合成下一档。下一档仍是一件，而且说得出：这两件合成之后多了哪一块、为什么是这个物件。换成一个同色但无关的物件，没过。
4. 体量只大一圈。最低档占格子大半，最高档留边，不顶出格子，也不缩成中间一个小点。末档最大、零件最多。
5. 沿档位零件变多或剪影更复杂。`parts_add` 必须是具体零件。只写「更华丽 / 加光 / 特效」没过。同模只加特效没过。
6. 相邻两档的剪影家族不能相同，也不能只改一两个字冒充不同。

机读数字过了、合成说不通，仍然不算定稿。讨论定稿之后，才把这八行写成机读文件。文件要有 `tracks:`，每一行用这些英文键：`level`、`name`、`silhouette`、`scale_delta`、`scale_pct`、`parts_add`。`scale_pct` 单调递增（L1 ≥ 0.58，L8 ≤ 0.80，后一档必须大于前一档）。L1 的 `parts_add` 写 `—`，L2–L8 必须是具体零件。键名写错或少了 `scale_pct`，`relation-judge` 审不了。

新任务另写一份副本，照 `docs/showcase/skill_full_modes_1027/merge_phase1_canonical.yaml` 的结构。不要改掉这份 canonical 里已有的 track。然后必须跑：

```bash
python pmem_art.py merge relation-judge --file <yaml> --all
```

**exit 0 才能出图。** 8 稿仍不过，停在这一段，不进入第二段。

关系过了，每一档单独出一张正方形核对。对不上就只改那一档，不重选八件。然后跑 `merge audit`。没过可以 `merge normalize` 一次再 audit。仍不过就逐格重出，不要靠归一化交差。audit 没过，不能进第二段。

## 第二段 · 美术

只从第一段过关的正方形接着画，不重选八件。每一档仍是单独一张正方形。最多再 4 轮，合格线 ≥ 9.6，`converge start --scale medium`。表面那一句每轮原样保留。生图句不写光影张力、体积光、次表面散射。件数、顺序、档位大小继续锁着。

同一档继续修时，每一轮垫的是这一档第一张关系过关的正方形，只在提示词里改点名的那一处。不垫风格参考文件，不垫上一轮更高分的成图，也不把前几轮修正叠进同一段。

每轮先出图再看像素。向玩家写出五维分、不足、下一轮改点，并再查第一段的关系。第二段每一轮 judge 之后再跑一次 audit。关系还在、audit 过了、美术分 ≥ 9.6，才停。关系散了或 audit 没过，这一轮美术分再高也不算过。满 4 轮还没有两段都过的，留下美术最高且关系仍在、audit 也过的那些正方形；关系都不在了，就交付第一段那些过关的正方形。

```bash
python pmem_art.py merge audit --dir <目录> --phase1 <yaml> --track <域名>
```

用 `converge generate` 记生图，`converge judge` 记审图，结束时 `converge finish`。

## 禁止

- 没过 `relation-judge` 就出图或上展示。
- 把八件画进同一张当成品。
- 从同框预览里抠图代替逐格重出。
- 垫风格参考文件，或让 L2–L8 全部垫 L1 来锁占格。
""",
    },
]
