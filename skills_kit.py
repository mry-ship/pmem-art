#!/usr/bin/env python3
"""
pmem-art skills_kit:
1. 定义并自动安装面向 Cursor / Claude Code / Codex 的美术技能（含 improve/coach/learn）（Skills & Slash Commands）：
   - /pmem-draw    (别名 /art-draw)    : 8轮 9.5分 闭环自评收敛生图（支持纯文本或【丢入参考图】先解构再生图 + 最终汇总评分表）
   - /pmem-style-lock (别名 /art-style): 样张/参考图一键提炼风格圣经与色板锁定
   - /pmem-critique (别名 /art-check)  : 单图/批量图主美级五维审稿与红线入库
   - /pmem-variant (别名 /art-variant) : 同角色/同资产跨画风分叉（Q版/水彩/像素）与表情动作差分
   - /pmem-atlas   (别名 /art-map)     : 一键归档散图、体检并刷新可视化图谱 art-atlas.html
   - /pmem-ui      (别名 /art-ui)      : SpriteCook 式 UI Kit / HUD / 九宫格整套生成 + 8轮9.5收敛
   - /pmem-concept (别名 /art-concept) : ZHO/Yolain/Comfy-FLUX 式概念图/Key Art 生成 + 8轮9.5收敛
   - /pmem-icon    (别名 /art-icon)    : jezweb 式一致化图标集 / SVG 取向生成 + 8轮9.5收敛

2. 提供 `pmem_art.py converge` 闭环收敛状态机与评分表生成器：
   - 记录第 1..8 轮生图的路径、五维评分、合理亮点、不合理缺陷与下一轮叠加修正指令
   - 判定 `>= 9.5` 立即达标收敛；若满 8 轮仍 `< 9.5`，自动挑选全阶段最高分轮次胜出
   - finish 默认静默自动驾驶（写反思/口味/learn 队列），只吐一行「小提示」；`--verbose` 才打全量 Markdown 总表
"""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


def _now_cst() -> datetime:
    return datetime.now(timezone(timedelta(hours=8)))


SKILL_SPECS: list[dict[str, Any]] = [
    {
        "name": "pmem-draw",
        "alias": "art-draw",
        "title": "【强制8轮≥9.5收敛】通用生图（纯文本/垫图 · 打分挑刺 · 汇总表）",
        "description": (
            "当用户输入 /pmem-draw 或 /art-draw（如「/pmem-draw 生成一张xxx风格的xxx图」或「/pmem-draw [附带一张图] 生成一张xxx图」）时触发。"
            "执行「先查记忆/分析参考图 → 生成1张图 → 严苛五维自评打分+指出不合理处 → 未达9.5分则叠加修正继续生图（最多8轮）→ "
            "达标或满8轮挑最高分 → 输出全轮次评分优劣汇总表并沉淀记忆」的完整闭环。"
        ),
        "body": r"""# `/pmem-draw`（别名 `/art-draw`）— 8轮 9.5分 闭环自评收敛生图技能

你现在运行在 **pmem-art 闭环自评收敛生图模式**。无论是纯文字生图还是用户丢入了一张参考图，你都必须严格执行以下闭环流程，**绝不能只生一张图就草草交差**（除非第 1 轮真实严苛评分就达到 `>= 9.5`）。

---

## 一、支持两种触发方式

### 方式 A：纯文本指令生图
> 例：`/pmem-draw 生成一张东方青瓷水彩风格的阿斯特拉半身立绘`
- 直接进入 **Step 1（召回记忆）→ Step 2（最多8轮自评收敛循环）→ Step 3（输出汇总表与沉淀记忆）**。

### 方式 B：丢入一张参考图 / 垫图 + 生成指令
> 例：`/pmem-draw [附带一张图] 生成一张同风格但换成冰霜刀光特效的武器图标`
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
   python3 pmem_art.py converge start --goal "<用户目标描述>" --module <目标模块> [--mode quality|fast] [--ref-image <参考图>] [--ref-analysis "<参考图分析>"]
   ```
   - 默认 `--mode quality` = 完整 8×≥9.5。
   - `--mode fast`：warm-start 置信度高时可走 **fast track**（仍须每张打分；最终采纳默认仍要 ≥9.5，除非用户明确说「草稿/fast/先看看」）。
   - 把打印出的 **Warm-Start `prompt_block` 完整并入第 1 轮 Prompt**。
3. **可选 Best-of-N 首帧**：第 1 轮先构思 2~3 个方向（或并行想法），挑最佳进入后续 converge（在回复里写明选了哪条）。

---

### Step 2：闭环自评收敛循环（最多 8 轮，合格线 `>= 9.5 / 10.0`）

令轮次 $i = 1, 2, \dots, 8$：

#### 2.1 生成第 $i$ 轮单张候选图
- 综合「用户原始需求 + 参考图解构特征（若有）+ `.memory-art` 历史红线 + **前 $i-1$ 轮累积的修正指令**」，构造第 $i$ 轮生图 Prompt。
- 调用生图工具（如 `GenerateImage` 或项目配置的生图脚本）**生成 1 张图**。

#### 2.2 严苛自我审图与五维打分（满分 `10.0` 分，精确到 `0.1`）
生成后，你**必须亲自检视这张生成图**，按以下 5 个维度客观、严苛打分（严禁敷衍给高分，有任何明显结构/透视/风格瑕疵都必须扣分）：
1. **风格与色板契合度（满分 2.5）**：是否符合目标画风与色板？有没有混入廉价塑料感、错误赛博霓虹或脏色？
2. **构图、透视与结构合理性（满分 2.5）**：头身比是否准确？手部/手指/五官/关节/器械对称性是否合理？UI 九宫格中心区是否干净？
3. **光影、材质与细节完成度（满分 2.0）**：光源方向是否统一？材质高光与暗部层次是否清晰？边缘有无杂边/毛刺？
4. **历史红线与管线规格合规度（满分 1.5）**：是否避开了 `style_redline`？透明底/宽高比是否符合预期？
5. **意图还原与参考图继承度（满分 1.5）**：是否精准表达了用户想要的动作/氛围/垫图神韵？

计算总分：`score = d1 + d2 + d3 + d4 + d5`（满分 `10.0`）。

#### 2.3 说出本张图的【合理亮点】与【不合理之处】，记录到收敛器
每一轮生成后，向用户简明汇报本轮得分、哪里画得好、**哪里不合理需要改**，并运行：
```bash
python3 pmem_art.py converge round \
  --round <i> \
  --image "<第i轮图片路径>" \
  --score <总分，如 8.6> \
  --dims "<五维明细，如 风格2.2/结构2.0/光影1.7/合规1.4/还原1.3>" \
  --strengths "<本轮合理与亮眼之处>" \
  --defects "<本轮不合理与缺陷之处（具体到部位/色彩/构图）>" \
  --next-fix "<下一轮叠加修正策略（具体要改什么提示词/加什么负向词/调什么结构）>" \
  --prompt "<本轮实际使用的 Prompt>"
```

#### 2.4 收敛判定（核心规则！）
- **情况 1：本轮评分 `>= 9.5`**
  🎉 **合格达标！** 立即结束生图循环，以第 $i$ 轮图片作为最终胜出图，进入 Step 3。
- **情况 2：本轮评分 `< 9.5` 且 $i < 8$**
  🔄 **不合格！** 必须把本轮找出的「不合理之处」转化为具体的叠加修正指令（Overlay Fix），并入第 $i+1$ 轮 Prompt（保留已画对的优点，专门修补本轮缺陷），**立即继续生第 $i+1$ 张图**。
- **情况 3：已满 8 轮（$i = 8$）且评分仍 `< 9.5`**
  🏁 **达到 8 轮上限，停止循环！** 从第 1 ~ 8 轮中**挑选综合评分最高的那一轮图片**作为最终交付图，进入 Step 3。

---

### Step 3：结算最优图、输出全轮次评分对比表 & 自动沉淀记忆

循环结束后，运行：
```bash
python3 pmem_art.py converge finish --apply
```
该命令会自动：
1. 选出达标轮次（`>= 9.5`）或全阶段最高分轮次（`Best of 8`）。
2. 将最终胜出图通过 `ingest` / `feedback` 写入 `.memory-art` 的 `recipe`（正向定稿锚点），并把迭代过程中暴露的典型不合理点写入 `style_redline` / `visual_correction`。
3. 生成标准 Markdown 汇总表。

**对用户的默认展示（静默自动驾驶 · Whisper）：**
1. 🏆 **最终胜出图** + 一句结论（第几轮达标 / 满8轮最高分）。
2. 💡 若 CLI 打出一行 **「小提示」**（如「下次注意：头身比」/「已记住：不要过曝高光」），**原样转述给用户**——整次会话最多 1 条，不要扩写成教练长文。
3. **禁止**向用户旁白「正在写反思 / 更新 taste / 入队 learn / 沉淀红线」；这些已在 `finish --apply` 后台静默完成。
4. 用户没要详情时，**不要**倾倒全轮次评分总表、本轮可学清单、improve/coach/learn 推销。需要全量时让用户加 `--verbose` 或主动说「看报告 / 进步 / 教练」。

### Agent 后台（对用户不可见）
`finish --apply` 已自动：写 recipe/红线 + 会话反思 + `run_silent_autopilot`（更新 taste、强化配方、悄悄 enqueue 1–2 条 learn 建议）。

### 闭环总览（用户几乎无感）
`装上就用 → 画 → 偶尔一行小提示 → 系统自己变强；进阶 peek：improve/coach/learn/progress/--verbose`
## 静默自动驾驶（Agent 必读 · 对用户几乎无感）
- `converge finish --apply` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-improve` / `/pmem-learn`。
- 对用户只展示：**胜出图 + 结论**；若 stdout 有「小提示」则原样转述（每会话最多 1 条）。
- **不要**叙述「已写入记忆 / 正在自我迭代 / 建议你跑 coach」。用户想看详情时用 `/pmem-progress`·`/pmem-coach`·`--verbose`（进阶/可选）。
""",
    },
    {
        "name": "pmem-style-lock",
        "alias": "art-style",
        "title": "参考图/样张一键提炼风格圣经与色板锁定",
        "description": (
            "当用户输入 /pmem-style-lock 或 /art-style 并附带样张/参考图时触发。"
            "自动解构样张的主辅色板 HEX、光影法则、笔触特征与禁用词，一键锁定为项目或模块的风格基准（art_decision + recipe）。"
        ),
        "body": r"""# `/pmem-style-lock`（别名 `/art-style`）— 样张提炼风格圣经与色板锁定

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
        "alias": "art-check",
        "title": "单图/批量图主美级五维审稿与红线入库",
        "description": (
            "当用户输入 /pmem-critique 或 /art-check 对现有图片进行审稿挑刺时触发。"
            "对照项目历史红线与模块规格进行五维打分，指出不合理之处，并可将问题一键记入 style_redline。"
        ),
        "body": r"""# `/pmem-critique`（别名 `/art-check`）— 主美级五维审稿与红线入库

当用户丢入一张或多张图让 Agent「审一下 / 看看哪里不合理 / 打个分」时执行：

1. **召回模块基准**：
   - 运行 `python3 pmem_art.py search --module <模块>` 获取已有红线、色板与管线规格。
   - 运行 `python3 pmem_art.py classify <图片路径>` 获取分辨率、宽高比、Alpha 透明通道等物理参数。
2. **五维打分与挑刺（满分 10.0 分）**：
   - 从「风格色板 (2.5) / 结构透视 (2.5) / 光影材质 (2.0) / 管线与红线合规 (1.5) / 设定还原 (1.5)」五个维度打分。
   - 明确列出 **✅ 合理亮点** 与 **❌ 不合理/需返修点**，并给出可直接用于下一轮重绘的 **修正 Prompt 建议**。
3. **自动沉淀红线**：
   - 若评分 `< 9.5` 或用户认可某条挑刺结论，调用 `python3 pmem_art.py feedback "<具体不合理点>" --module <模块> --asset <图片路径>` 自动写入记忆库。
4. **静默默认**：向用户最多一句「小提示」（如「下次注意：光影」）；完整教练报告仅当用户明确要 `/pmem-coach` 或 `--verbose`。
""",
    },
    {
        "name": "pmem-variant",
        "alias": "art-variant",
        "title": "同角色/同资产跨画风分叉（水彩/Q版/像素）与表情动作差分",
        "description": (
            "当用户输入 /pmem-variant 或 /art-variant 要求基于已有角色/资产生成其他画风（Q版/水彩/像素）或表情/动作差分时触发。"
            "自动继承父模块核心视觉锚点并建立独立子模块，做到换画风不丢人设。"
        ),
        "body": r"""# `/pmem-variant`（别名 `/art-variant`）— 跨画风分叉与表情/动作差分生成

当用户希望把已有角色/物件衍生出新画风（如「把 Astra 做成 Q 版贴纸 / 水彩概念图」）或做差分（如「生成愤怒/惊讶表情差分」「生成 4 帧挥刀序列帧」）时执行：

1. **读取父模块核心锚点**：
   - 运行 `python3 pmem_art.py search --module <父模块，如 character.Astra>`。
   - 锁定不可改变的**人设核心识别特征**（发色、瞳色、标志性配饰如左眼黄铜星盘义眼、主色板）。
2. **确定子模块与规格适配**：
   - 画风分叉：如 `character.Astra.Chibi`（2~3头身、允许大头萌化）、`character.Astra.Watercolor`（允许非透明纸本纹理底 `alpha_required: false`）。
   - 差分/动画：如 `character.Astra.Expressions`（严格锁死五官比例与底图机位）、`anim.Astra` 或 `vfx.*`（整除序列帧网格 + 透明底）。
3. **调用自评收敛生图并独立归档**：
   - 按 9.5 分标准生成与自评，完成后运行 `python3 pmem_art.py ingest <新图路径> -p "<含角色名+画风/差分词的Prompt>" --apply` 自动创建子模块并归位。
""",
    },
    {
        "name": "pmem-atlas",
        "alias": "art-map",
        "title": "一键归档散图、记忆体检并刷新可视化图谱工作台",
        "description": (
            "当用户输入 /pmem-atlas 或 /art-map 时触发。"
            "自动扫描归位未分类散图、运行管线与记忆过期体检，并重新生成 art-atlas.html。"
        ),
        "body": r"""# `/pmem-atlas`（别名 `/art-map`）— 整理散图与刷新可视化图谱

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
        "alias": "art-ui",
        "title": "【强制8轮≥9.5收敛】SpriteCook式 UI Kit/HUD/九宫格整套",
        "description": (
            "【截图可见·必读】/pmem-ui 与 /art-ui 生成 UI Kit/HUD 时，概念稿与关键组件均强制「最多8轮、合格线≥9.5」闭环自评收敛（生1张→打分挑刺→<9.5叠加修正→满8轮挑最高分→评分总表）。"
            "流水线对标 SpriteCook：概念先行 → 透明组件表 → 九宫格切线 → 状态族。"
            "触发例：「/pmem-ui 生成一套蒸汽朋克主菜单 HUD」「/art-ui [附概念图] 拆出九宫格弹窗与按钮态」。"
        ),
        "body": r"""# `/pmem-ui`（别名 `/art-ui`）— SpriteCook 式 UI Kit / HUD / 九宫格整套生成

## 怎么用（复制即用）
```text
/pmem-ui 生成一套青瓷幻想风主菜单：九宫格面板 + 按钮 normal/pressed/disabled
/art-ui 做一套蒸汽朋克战斗 HUD（血条空满、技能槽），透明底
/pmem-ui [拖入概念图] 按概念拆出主面板九宫格、主按钮四态、进度条空/满、Tab 两态
```

## 原理（截图摘要）
1. `search` 召回 `ui.*` 红线与定稿 → 2. **概念先行** → 3. 透明组件表 → 4. 九宫格 + 状态族 → 5. **强制 8轮 ≥9.5** → `finish` **静默自动驾驶**（只转述一行小提示；勿旁白记忆写入）

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
2. 若无概念图：先生成 **1 张完整屏幕概念稿**（整屏布局，统一材质与色板），用 `/pmem-draw` 同款 **8轮 >=9.5 收敛** 打磨概念稿：
   ```bash
   python3 pmem_art.py converge start --goal "UI概念稿：<屏幕类型+风格>" --module <ui.模块>
   # … 每轮 converge round … 直到 >=9.5 或满8轮挑最高分
   python3 pmem_art.py converge finish --apply
   ```
3. **概念稿通过后才进入组件表**——不要在概念未锁定时散生按钮。

### Step 2：从概念抽取组件表（Component Sheets）
以概念稿为垫图/参考，在 **透明底** 上生成组件表（1~3 张 sheet），覆盖：
- **面板 / 边框 / 装饰条**（可九宫格拉伸）
- **按钮族**：至少 normal + pressed（最好含 hover / disabled）
- **进度条 / 血条**：空轨 + 满轨（或分段填充）
- **标签 / Tab**：选中 + 未选中
- **图标位 / 分隔线 / 角花** 等概念中出现或隐含的零件
同一概念参考下批量生成，保证木纹/螺栓/色板/光影角度一致。缺件时只补缺件，不要整套重开。

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
对主面板、主按钮等核心件，若五维评分 `< 9.5`（重点查：中心拉伸区是否干净、转角是否形变、透明底毛边、状态族是否同系），再跑一轮 `converge` 局部重绘。

### Step 5：沉淀记忆
```bash
python3 pmem_art.py ingest <concept或主面板路径> -p "UI kit <屏幕> 概念/主面板" --apply
python3 pmem_art.py feedback "UI套件色板与九宫格规范：<摘要>" --module <ui.模块> --kind art_decision
```

## 三、UI 专用五维评分侧重（满分 10.0，`>= 9.5` 合格）
1. 风格色板契合（2.5）— 与概念稿同材质同色板
2. 结构/九宫格合理性（2.5）— 中心区干净、角不糊、可拉伸
3. 光影材质完成度（2.0）
4. 红线与管线合规（1.5）— RGBA 透明底、分辨率、无脏边
5. 套件一致性 / 状态族完整（1.5）— normal/pressed 等同系，不「各画各的」

## 四、最终交付必须包含
1. 概念稿 + 组件表 + `elements/` + `manifest.json`（含九宫格）
2. 若跑了收敛：全轮次评分优劣总表
3. 已写入 `.memory-art` 的 recipe / redline 路径


## 静默自动驾驶（Agent 必读）
- `converge finish --apply` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户只展示胜出图 + 结论；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 全量报告 / 教练 / 广度：用户明确要求或 `--verbose` / 进阶技能时再给。
""",
    },
    {
        "name": "pmem-concept",
        "alias": "art-concept",
        "title": "【强制8轮≥9.5收敛】原画/概念图/Key Art（ZHO·FLUX式完整句Prompt）",
        "description": (
            "【截图可见·必读】/pmem-concept 与 /art-concept（原画/概念图/Key Art）与 /pmem-draw 一样，强制执行「最多8轮、合格线≥9.5分」闭环自评收敛："
            "生1张→五维打分+指出不合理处→<9.5则叠加修正继续生→达标即停或满8轮挑最高分→输出全轮次评分表并沉淀记忆。"
            "触发例：「/pmem-concept 画一张青瓷废土主视觉Key Art」「/art-concept [附参考] 同氛围气氛图」。"
            "Prompt 采用 ZHO/Yolain/Comfy-FLUX 式完整自然语言句（主体靠前、正向写排斥项）。"
        ),
        "body": r"""# `/pmem-concept`（别名 `/art-concept`）— 原画 / 概念图 / Key Art

> ⚠️ **【强制闭环 · 与 `/pmem-draw` 同等】**  
> 本技能生成原画/概念图/Key Art 时，**必须**跑满同一套收敛规则：  
> **最多 8 轮生图 · 合格线 `≥ 9.5 / 10.0` · 未达标叠加修正继续生 · 满 8 轮挑全阶段最高分 · 最终输出评分优劣总表并写入 `.memory-art`**。  
> **禁止只生一张图就交差**（除非第 1 轮真实严苛评分就 ≥ 9.5）。

## 怎么用（复制即用）
```text
/pmem-concept 画一张东方青瓷废土的主视觉 Key Art，宽幅海报，电影感侧逆光
/art-concept 生成一张浮空遗迹黄昏气氛概念图，青瓷白+墨蓝+鎏金
/pmem-concept [拖入参考图] 保持构图与色板，画一张同世界观角色登场 Key Art
```

## 原理（截图摘要）
1. **Warm-Start + 与 draw 同等 8×≥9.5** → 2. `search`/口味召回 → 3. **FLUX 完整句** → 4. 垫图解构 → 5. `converge` → 6. `finish` 静默自动驾驶（一行小提示；improve/learn 为进阶 peek）

你现在运行在 **pmem-art 原画 / 概念图 / Key Art 模式**（对标 ZHO Comfy-FLUX 与 Yolain 等 FLUX 系提示法）：用 **完整自然语言句子** 描述成片，**主体与构图靠前**；FLUX 系几乎无有效负向 Prompt，排斥项用正向措辞写进正文。

---

## 一、适用场景
- 主视觉 Key Art / 宣传海报 / 场景气氛图 / 角色概念设定 / 封面插画
- 需要电影感光影、叙事构图、高完成度单帧，而非 UI 切图或 SVG 图标

## 二、FLUX 系 Prompt 写法（必须遵守）
1. **完整句，不要纯 tag 堆砌**；T5/CLIP-L 对句子更友好。
2. **权重靠前**：先写主体与动作，再场景，再风格/光影/色板，再画幅与成片要求。
3. **无负向列表**：把「不要霓虹紫」写成「干净的青瓷白与墨蓝，无霓虹」。
4. **可选结构模板**：
   ```
   [主体与动作]。[场景与空间关系]。[光影与时段]。[材质与画风]。
   [色板：主色…辅色…点缀…]。[构图/景别/画幅]。[成片质量：边缘清晰、无水印无文字…]
   ```

## 三、标准流程（Memory → Prompt → Converge）

### Step 0：垫图（可选）
若用户丢入参考图：输出构图/色板 HEX/光影/笔触解构，写入 `converge start --ref-image … --ref-analysis …`。

### Step 1：召回记忆并开收敛会话
```bash
python3 pmem_art.py search --module <scene.|character.|brand.模块>
python3 pmem_art.py converge start --goal "<概念图目标>" --module <模块> [--ref-image …] [--ref-analysis …]
```

### Step 2：最多 8 轮自评收敛（合格线 `>= 9.5`）
每轮：
1. 用上一轮缺陷的 **正向叠加修正** 重写完整句 Prompt（仍禁止只堆 negative tags）。
2. 生成 **1 张** 概念图 / Key Art。
3. 五维严苛打分 + 说出合理处与不合理处 → `converge round`。
4. `>= 9.5` 立即停；`< 9.5` 且未满 8 轮则继续；满 8 轮挑最高分。

**概念图五维侧重**：
1. 风格色板（2.5）2. 构图叙事与透视（2.5）3. 光影材质（2.0）4. 红线合规（1.5）5. 氛围/意图还原（1.5）

### Step 3：结算与沉淀
```bash
python3 pmem_art.py converge finish --apply
```
向用户展示：胜出图、全轮次评分表、最终 Prompt 全文、已写入的 recipe/redline。

## 四、与 `/pmem-draw` 的分工
- **`/pmem-draw`**：通用单图收敛（角色立绘、道具、单件 UI 等）
- **`/pmem-concept`**：专门服务 **概念图 / Key Art / 气氛图**，强制 FLUX 式完整句 Prompt 与叙事构图标准


## 静默自动驾驶（Agent 必读）
- `converge finish --apply` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户只展示胜出图 + 结论；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 全量报告 / 教练 / 广度：用户明确要求或 `--verbose` / 进阶技能时再给。
""",
    },
    {
        "name": "pmem-icon",
        "alias": "art-icon",
        "title": "【强制8轮≥9.5收敛】jezweb式一致化图标集/SVG",
        "description": (
            "【截图可见·必读】/pmem-icon 与 /art-icon 生成图标集时，关键单枚与不合格批次强制「最多8轮、合格线≥9.5」闭环自评收敛（生1张→打分挑刺→<9.5叠加修正→满8轮挑最高分→评分总表）。"
            "流水线对标 jezweb：先锁 style-spec → 约5个一批 SVG（统一 viewBox/currentColor/stroke）→ preview.html。"
            "触发例：「/pmem-icon 给青瓷RPG做一套24px导航图标」「/art-icon home settings inventory」。"
        ),
        "body": r"""# `/pmem-icon`（别名 `/art-icon`）— jezweb 式一致化图标集 / SVG 取向生成

## 怎么用（复制即用）
```text
/pmem-icon 给本项目做一套 24px Clean 预设导航+背包图标（SVG），输出 style-spec 与 preview.html
/art-icon home settings inventory craft map quest
/pmem-icon [拖入品牌样张] 按这个线宽与圆角补齐：phone email location
```

## 原理（截图摘要）
1. 先锁 **style-spec** → 2. SVG 硬规则 → 3. 分批生成 → 4. 交付 preview → 5. 关键枚 **Warm-Start + 8×≥9.5** → 6. 反思 / improve / learn 扩图标技法卡

你现在运行在 **pmem-art 图标集模式**（对标 jezweb `icon-set-generator`）：先锁 **一份 style-spec**，再批量生成，保证 stroke、圆角、视口、视觉重量一致——**禁止**从 Lucide/Heroicons 随便拼一套「看起来差不多」的通用库图标冒充项目定制集。

---

## 一、适用场景
- 网站 / App / 游戏 HUD 的 **成套自定义图标**
- 需要 SVG（优先）或统一栅格（如 64×64 透明底道具图标）且 **整套同系**

## 二、标准流程（Brief → Spec → Batch → Review → Converge）

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

若用户要的是 **游戏道具栅格图标**（非 SVG）：仍先锁「线宽/圆角/色板/投影」style-spec，再批量生成透明底 PNG，规则改为「同色板同描边同投影」，并可用 `converge` 打磨单枚。

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

### Step 5：关键图标 8轮9.5 收敛（可选）
用户点名某枚「不对」或一致性审查不通过时：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module ui.Icons
# 生成 → 自评（侧重：规格一致性 2.5 + 识别度 2.5 + …）→ round → finish --apply
```

### Step 6：沉淀
```bash
python3 pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module ui.Icons --kind art_decision
python3 pmem_art.py ingest icons/preview.html -p "icon set preview" --apply   # 若适用
```

## 三、交付检查清单
- [ ] 全部 SVG 同 viewBox / stroke-width / linecap / linejoin
- [ ] 全部 `currentColor`
- [ ] 视觉重量平衡、padding 一致、光学居中
- [ ] 文件名 kebab-case；`preview.html` + `style-spec.json` 齐全
- [ ] 若跑了收敛：胜出图 + 一行小提示即可（全表仅 --verbose）

## 静默自动驾驶（Agent 必读）
- `converge finish --apply` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户只展示胜出图 + 结论；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 全量报告 / 教练 / 广度：用户明确要求或 `--verbose` / 进阶技能时再给。
""",
    },
    {
        "name": "pmem-improve",
        "alias": "art-improve",
        "title": "【进阶/可选】自我迭代 peek：反思→口味→进步（日常已静默自动驾驶）",
        "description": (
            "当用户说「提升/自我迭代/总结这次/越用越好」或输入 /pmem-improve /art-improve 时触发。"
            "扫描会话反思与反馈红线，更新个人口味档案 taste.json，并汇报进步曲线。"
        ),
        "body": r"""# `/pmem-improve`（别名 `/art-improve`）— 【进阶/可选】自我迭代 peek

> **日常不用喊这个。** `converge finish` / 高信号 `feedback` 后系统已**静默自动驾驶**：写反思、更新口味、强化配方、排队知识建议，最多一行「小提示」。

## 什么时候用
想**主动偷看**进步曲线、口味档案变了什么时：
```text
/pmem-improve
/art-improve 总结最近几次，看看我哪里变强了
```

## 原理
`finish --apply` → 反思 JSON + silent autopilot → taste.json；本技能只是把后台已经做过的事**大声读一遍**。

```bash
python3 pmem_art.py improve run          # 完整报告（peek）
python3 pmem_art.py progress             # 进步曲线
python3 pmem_art.py taste show
python3 pmem_art.py coach                # 能力教练（进阶）
```
""",
    },
    {
        "name": "pmem-coach",
        "alias": "art-coach",
        "title": "【进阶/可选】能力教练 peek：短板→练习→下一张目标",
        "description": (
            "当用户输入 /pmem-coach 或 /art-coach，或说「练什么/我的短板/能力提升计划」时触发。"
            "把红线与会话反思归类为构图/光影/解剖/九宫格等能力维，输出个人练习计划与下一张绘制目标。"
        ),
        "body": r"""# `/pmem-coach`（别名 `/art-coach`）— 【进阶/可选】能力教练 peek

> 日常收敛只会给一行「小提示」。本技能用于你**主动要练习计划**时。

## 怎么用
```text
/pmem-coach
/art-coach 我最近老是翻车，给我练习计划
```

## 原理
红线 + `_reflections/` → 短板类别 → drills → `next_draw_goals`。

```bash
python3 pmem_art.py coach
python3 pmem_art.py progress
```
""",
    },
    {
        "name": "pmem-learn",
        "alias": "art-learn",
        "title": "【进阶/可选】知识广度 peek：技法/光影/镜头/UI 卡片（finish 已静默 enqueue）",
        "description": (
            "当用户输入 /pmem-learn 或 /art-learn，或说「扩展知识/学新技法/补广度」时触发。"
            "根据已有域与缺口提出 3~5 条广度扩展（技法卡/风格分叉/相邻模块种子），接受后写入 .memory-art/_knowledge/。"
        ),
        "body": r"""# `/pmem-learn`（别名 `/art-learn`）— 【进阶/可选】知识广度 peek

> `finish` 后已**静默 enqueue** 1–2 条建议到 `learn_proposals.json`。本技能用于查看/接受/补提更多。

## 怎么用
```text
/pmem-learn
/art-learn 看看排队的知识卡
```

```bash
python3 pmem_art.py learn suggest          # 大声列出建议（peek）
python3 pmem_art.py learn accept --all
python3 pmem_art.py learn list
```
""",
    },
]


def _render_skill_md(spec: dict[str, Any], command_name: str) -> str:
    return (
        f"---\n"
        f"name: {command_name}\n"
        f"description: {spec['description']}\n"
        f"---\n\n"
        f"{spec['body'].strip()}\n"
    )


def _render_command_md(spec: dict[str, Any], command_name: str) -> str:
    return (
        f"---\n"
        f"description: {spec['title']}（pmem-art）\n"
        f"---\n\n"
        f"{spec['body'].strip()}\n"
    )


AGENT_DOC_MARKER_START = "<!-- pmem-art:skills:start -->"
AGENT_DOC_MARKER_END = "<!-- pmem-art:skills:end -->"


def _render_agent_doc_block() -> str:
    return f"""{AGENT_DOC_MARKER_START}
## 🎨 pmem-art 美术记忆系统与内置斜杠技能（Skills）

本项目挂载了 **pmem-art**（面向 Cursor / Claude Code / Codex 的个人美术积累记忆与闭环自评生图系统）。

### 1. 内置快捷技能（在对话框直接输入 `/技能名` 即可触发）

| 技能指令 | 简短别名 | 用途说明 |
| :--- | :--- | :--- |
| **`/pmem-draw`** | **`/art-draw`** | **【强制 8轮 ≥9.5 收敛】** 通用生图：纯文本或垫图 → 生1张→打分挑刺→`<9.5`叠加修正→满8轮挑最高分→评分总表 |
| **`/pmem-ui`** | **`/art-ui`** | **【强制 8轮 ≥9.5 收敛】** SpriteCook 式 UI Kit/HUD/九宫格：概念先行→组件表→9-slice→状态族 |
| **`/pmem-concept`** | **`/art-concept`** | **【强制 8轮 ≥9.5 收敛】** 原画/概念图/Key Art（ZHO·FLUX 完整句 Prompt）— **与 draw 同等强制闭环，禁止只生一张** |
| **`/pmem-icon`** | **`/art-icon`** | **【强制 8轮 ≥9.5 收敛】** jezweb 式一致化 SVG 图标集：style-spec→分批→preview；关键枚强制收敛 |
| **`/pmem-style-lock`** | **`/art-style`** | **样张一键提炼风格圣经与色板锁定**：丢入样张提取 HEX 色板、光影笔触与禁用词，锁定进项目记忆 |
| **`/pmem-critique`** | **`/art-check`** | **主美级五维审稿与红线入库**：对照项目记忆给图片打分挑刺，并将翻车点记入 `style_redline` |
| **`/pmem-variant`** | **`/art-variant`** | **跨画风分叉与表情/动作差分**：继承角色核心锚点，派生水彩/Q版/像素子模块或序列帧差分 |
| **`/pmem-atlas`** | **`/art-map`** | **一键整理散图并刷新 `art-atlas.html` 可视化图谱** |
| **`/pmem-improve`** | **`/art-improve`** | **【进阶 peek】** 自我迭代报告（日常 finish 已静默跑） |
| **`/pmem-coach`** | **`/art-coach`** | **【进阶 peek】** 能力教练练习计划 |
| **`/pmem-learn`** | **`/art-learn`** | **【进阶 peek】** 知识广度建议（finish 已静默 enqueue） |

### 2. 静默自动驾驶（默认）
- `converge finish --apply` 与高信号 `feedback` 后：自动写反思、更新 taste、强化 recipe/红线、悄悄排队 learn——对用户最多一行「小提示」。
- Agent **不要**旁白记忆写入；全量报告用 `--verbose` 或上述进阶技能。

### 3. 日常自然语言反馈沉淀（无需手写 YAML）
- 生图前先运行：`python3 pmem_art.py search --module <模块>` 或 `python3 pmem_art.py search "<关键词>"`
- 当画师说「太赛博 / 头太大 / 别这样画 / 这版留着 / 换成水彩 / 以后都用…」时，立即运行：
  `python3 pmem_art.py feedback "<画师原话>" --module <模块> [--asset <图片路径>]`
- 运行闭环收敛追踪器：`python3 pmem_art.py converge start|round|finish`（finish 默认静默）
{AGENT_DOC_MARKER_END}
"""


def _upsert_markdown_block(file_path: Path, header_title: str) -> None:
    block = _render_agent_doc_block()
    if file_path.exists():
        content = file_path.read_text(encoding="utf-8")
        if AGENT_DOC_MARKER_START in content and AGENT_DOC_MARKER_END in content:
            pre = content.split(AGENT_DOC_MARKER_START)[0]
            post = content.split(AGENT_DOC_MARKER_END)[1]
            file_path.write_text(pre.rstrip() + "\n\n" + block + "\n" + post.lstrip(), encoding="utf-8")
        else:
            file_path.write_text(content.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
    else:
        file_path.write_text(f"# {header_title}\n\n{block}\n", encoding="utf-8")


def install_skills_and_agent_configs(root: Path, quiet: bool = False) -> dict[str, list[str]]:
    """
    在目标项目根目录自动安装：
    - Cursor Skills & Slash Commands: .cursor/skills/<name>/SKILL.md, .cursor/commands/<name>.md
    - Claude Code Skills & Commands : .claude/skills/<name>/SKILL.md, .claude/commands/<name>.md, CLAUDE.md
    - Codex / Agents Skills         : .agents/skills/<name>/SKILL.md, AGENTS.md
    """
    installed: dict[str, list[str]] = {
        "cursor_skills": [],
        "cursor_commands": [],
        "claude_skills": [],
        "claude_commands": [],
        "codex_skills": [],
        "agent_docs": [],
    }

    for spec in SKILL_SPECS:
        names = [spec["name"], spec["alias"]]
        for nm in names:
            # 1. Cursor skill & slash command
            c_skill = root / ".cursor" / "skills" / nm / "SKILL.md"
            c_skill.parent.mkdir(parents=True, exist_ok=True)
            c_skill.write_text(_render_skill_md(spec, nm), encoding="utf-8")
            installed["cursor_skills"].append(str(c_skill.relative_to(root)))

            c_cmd = root / ".cursor" / "commands" / f"{nm}.md"
            c_cmd.parent.mkdir(parents=True, exist_ok=True)
            c_cmd.write_text(_render_command_md(spec, nm), encoding="utf-8")
            installed["cursor_commands"].append(str(c_cmd.relative_to(root)))

            # 2. Claude Code skill & slash command
            cl_skill = root / ".claude" / "skills" / nm / "SKILL.md"
            cl_skill.parent.mkdir(parents=True, exist_ok=True)
            cl_skill.write_text(_render_skill_md(spec, nm), encoding="utf-8")
            installed["claude_skills"].append(str(cl_skill.relative_to(root)))

            cl_cmd = root / ".claude" / "commands" / f"{nm}.md"
            cl_cmd.parent.mkdir(parents=True, exist_ok=True)
            cl_cmd.write_text(_render_command_md(spec, nm), encoding="utf-8")
            installed["claude_commands"].append(str(cl_cmd.relative_to(root)))

            # 3. Codex (.agents/skills/<nm>/SKILL.md)
            cx_skill = root / ".agents" / "skills" / nm / "SKILL.md"
            cx_skill.parent.mkdir(parents=True, exist_ok=True)
            cx_skill.write_text(_render_skill_md(spec, nm), encoding="utf-8")
            installed["codex_skills"].append(str(cx_skill.relative_to(root)))

    # 4. Upsert CLAUDE.md and AGENTS.md
    claude_md = root / "CLAUDE.md"
    _upsert_markdown_block(claude_md, "CLAUDE.md — Project Instructions")
    installed["agent_docs"].append("CLAUDE.md")

    agents_md = root / "AGENTS.md"
    _upsert_markdown_block(agents_md, "AGENTS.md — Codex & Coding Agent Instructions")
    installed["agent_docs"].append("AGENTS.md")

    if not quiet:
        print(f"✨ 已自动安装 pmem-art {len(SKILL_SPECS)} 项美术技能（含别名共 {len(SKILL_SPECS)*2} 个斜杠入口）到 Cursor / Claude Code / Codex：")
        for spec in SKILL_SPECS:
            print(f"   · /{spec['name']:<16} (别名 /{spec['alias']:<11}) — {spec['title']}")
        print("   · 安装路径: .cursor/{skills,commands}/ · .claude/{skills,commands}/ · .agents/skills/ · CLAUDE.md · AGENTS.md")
    return installed


# ============================================================================
# 闭环自评收敛状态机 (`pmem_art.py converge`)
# ============================================================================

DEFAULT_THRESHOLD = 9.5
DEFAULT_MAX_ROUNDS = 8
FAST_SOFT_THRESHOLD = 9.0  # fast-track: prefer fewer regens when score>=9.0 & delta small; final accept still >=9.5 unless draft

CONVERGE_SCALE_PROFILES: dict[str, dict[str, Any]] = {
    "low": {
        "scale": "low",
        "label": "低强度 · 保守修瑕 (Defect-Fix Only)",
        "dim_weights": {
            "composition": 0.15,
            "lighting_color": 0.20,
            "perspective_anatomy": 0.25,
            "texture_detail": 0.25,
            "spec_style": 0.15,
        },
        "next_fix_budget": "conservative (<=20% prompt delta)",
        "max_prompt_delta_ratio": 0.20,
        "allow_recompose": False,
        "allow_lighting_overhaul": False,
        "min_round_leap": 0.15,
        "prompt_directive": (
            "【收敛强度: LOW (只修缺陷)】严格锁死参考原图/上一轮的镜头机位、主体姿态、构图重心与主光源方向，"
            "严禁增删配饰或改变环境构图；next_fix 仅针对五维审图发现的解剖结构瑕疵（五指/关节/五官对称）、"
            "边缘杂色或局部纸纹材质颗粒缺失做最小幅度靶向修补。"
        ),
    },
    "medium": {
        "scale": "medium",
        "label": "中强度 · 补足加小优化 (Balance & Polish)",
        "dim_weights": {
            "composition": 0.20,
            "lighting_color": 0.25,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.20,
            "spec_style": 0.15,
        },
        "next_fix_budget": "moderate (25%–45% prompt delta)",
        "max_prompt_delta_ratio": 0.45,
        "allow_recompose": False,
        "allow_lighting_overhaul": True,
        "min_round_leap": 0.35,
        "prompt_directive": (
            "【收敛强度: MEDIUM (补足加小优化)】保持原图核心主体与构图框架不变，主动结合全局底层技法卡补足原图短板："
            "强化 45° 侧逆光轮廓分离 (Rim Light)、补充皮肤次表面散射 (SSS) 与环境反射光 (Bounce Light)、"
            "拉开近中远三层大气透视，并精细化 300g 冷压纸纹/厚涂油画刀触等物理媒介质感。"
        ),
    },
    "high": {
        "scale": "high",
        "label": "高强度 · 大胆重构构图与光影 (Bold Creative Overhaul)",
        "dim_weights": {
            "composition": 0.25,
            "lighting_color": 0.30,
            "perspective_anatomy": 0.15,
            "texture_detail": 0.20,
            "spec_style": 0.10,
        },
        "next_fix_budget": "bold_overhaul (50%–80% prompt delta)",
        "max_prompt_delta_ratio": 0.80,
        "allow_recompose": True,
        "allow_lighting_overhaul": True,
        "min_round_leap": 0.55,
        "prompt_directive": (
            "【收敛强度: HIGH (允许重构构图与重做光影 · Showcase级跃升)】严禁停留在小修小补或平庸平移！"
            "在锁定原图核心艺术媒介与画风基因的前提下，next_fix 必须大胆重构画面张力：升级更具冲击力的电影级镜头构图"
            "（前景虚化压角/黄金螺旋视觉引导/戏剧化景别微调）、重做高反差冷暖戏剧光影（丁达尔体积光束/木漏日斑驳光影/"
            "强烈明暗交界线冷暖碰撞）并注入情绪叙事细节，实现远超原图与上一轮的视觉跃升。"
        ),
    },
    "recompose": {
        "scale": "recompose",
        "label": "定向改构图模式 · 用户指定新构图方向 (Directed Re-Composition)",
        "dim_weights": {
            "composition": 0.30,
            "lighting_color": 0.25,
            "perspective_anatomy": 0.20,
            "texture_detail": 0.15,
            "spec_style": 0.10,
        },
        "next_fix_budget": "directed_recompose (60%–85% prompt delta)",
        "max_prompt_delta_ratio": 0.85,
        "allow_recompose": True,
        "allow_lighting_overhaul": True,
        "min_round_leap": 0.50,
        "prompt_directive": (
            "【收敛强度: RECOMPOSE (用户指定改构图模式)】严格继承参考原图的画风笔触、媒介肌理、主辅色板与角色核心人设锚点，"
            "同时必须 100% 按照用户指定的构图改造方向（recompose_dir，如特写改全景、主体移至画面左侧三分点、平视改高空俯瞰等）"
            "彻底重排镜头机位、主体位置与空间景深层次。"
        ),
    },
}


def get_converge_scale_profile(scale: str = "medium", recompose_dir: str = "") -> dict[str, Any]:
    s = (scale or "medium").strip().lower()
    if recompose_dir and s not in ("recompose",):
        s = "recompose"
    if s not in CONVERGE_SCALE_PROFILES:
        s = "medium"
    prof = dict(CONVERGE_SCALE_PROFILES[s])
    if recompose_dir:
        prof["recompose_dir"] = recompose_dir
        prof["prompt_directive"] = prof["prompt_directive"] + f" 当前强制构图改造指令：【{recompose_dir}】。"
    return prof



def _session_file(root: Path, session_id: str = "latest") -> Path:
    d = root / ".memory-art" / "converge"
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{session_id}.json"


def cmd_converge(
    root: Path,
    data: dict[str, Any],
    action: str,
    *,
    session_id: str = "latest",
    goal: str = "",
    module: str = "",
    ref_image: str = "",
    ref_analysis: str = "",
    threshold: float = DEFAULT_THRESHOLD,
    max_rounds: int = DEFAULT_MAX_ROUNDS,
    round_num: int = 0,
    image: str = "",
    score: float = 0.0,
    dims: str = "",
    strengths: str = "",
    defects: str = "",
    next_fix: str = "",
    prompt: str = "",
    apply_memory: bool = True,
    converge_mode: str = "quality",
    scale: str = "",
    recompose_dir: str = "",
    draft_ok: bool = False,
    verbose: bool = False,
    silent: bool = True,
) -> int:
    """
    converge_mode: quality (default, full 8×≥9.5) | fast (warm-start fast-track hints).
    draft_ok: if True (user said 草稿/fast), final accept may use soft threshold in fast mode.
    silent: default True — finish/round 少说话，后台 autopilot；verbose=True 打全量报告。
    """
    if verbose:
        silent = False
    sf = _session_file(root, session_id)
    converge_mode = (converge_mode or "quality").lower()
    if converge_mode not in ("quality", "fast"):
        converge_mode = "quality"
    cfg_conv = (data.get("config") or {}).get("converge") if isinstance(data, dict) else {}
    if not isinstance(cfg_conv, dict):
        cfg_conv = {}
    eff_scale = (scale or cfg_conv.get("default_scale") or "medium").strip().lower()
    scale_prof = get_converge_scale_profile(eff_scale, recompose_dir=recompose_dir)
    eff_scale = scale_prof["scale"]

    if action == "start":
        if not module and goal:
            from feedback import infer_module_from_text
            module = infer_module_from_text(goal, data)

        from improve import build_warm_start_pack, print_warm_start, ingest_term_to_knowledge
        warm = build_warm_start_pack(root, data, module=module or "brand.GlobalStyle", goal=goal or "")
        print_warm_start(warm)

        # Grow knowledge from ref-analysis / goal terms
        for blob in (goal, ref_analysis):
            if blob:
                created = ingest_term_to_knowledge(root, blob, source="converge_start")
                if created:
                    print(f"🌍 知识广度：已触及/写入卡片 {', '.join(created)}")

        fast_track = bool(converge_mode == "fast" and warm.get("fast_track_eligible"))
        # In fast mode with high confidence, keep threshold 9.5 for final unless draft_ok
        eff_threshold = float(threshold)
        if draft_ok and converge_mode == "fast":
            eff_threshold = min(eff_threshold, FAST_SOFT_THRESHOLD)

        sess = {
            "session_id": session_id,
            "started_at": _now_cst().strftime("%Y-%m-%d %H:%M:%S UTC+8"),
            "goal": goal or "未命名生图任务",
            "module": module or "brand.GlobalStyle",
            "mode": "ref_image_guided" if ref_image else "text_guided",
            "converge_mode": converge_mode,
            "quality_mode": converge_mode,
            "scale": eff_scale,
            "scale_profile": scale_prof,
            "recompose_dir": recompose_dir,
            "fast_track": fast_track,
            "draft_ok": bool(draft_ok),
            "ref_image": ref_image,
            "ref_analysis": ref_analysis,
            "threshold": eff_threshold,
            "accept_threshold": float(threshold),  # hard rule for final unless draft
            "max_rounds": int(max_rounds),
            "status": "running",
            "rounds": [],
            "warm_start": warm,
            "lessons_all": [],
        }
        sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
        print(
            f"🎯 [收敛会话已启动] 模块: {sess['module']} | 模式: {converge_mode} | 强度(scale): {eff_scale} ({scale_prof['label']})"
            f"{' · FAST-TRACK' if fast_track else ''} | 合格线: >= {sess['accept_threshold']} 分"
            f"{'（草稿软线 ' + str(eff_threshold) + '）' if draft_ok else ''} | 最大轮次: {sess['max_rounds']}"
        )
        print(f"🎚️  Scale 内部权重与约束: weights={scale_prof['dim_weights']} | budget={scale_prof['next_fix_budget']}")
        print(f"🧭 Scale 指令: {scale_prof['prompt_directive']}")
        if fast_track:
            print(
                f"⚡ Fast-track：warm-start 置信 {warm.get('confidence')} 高。"
                f"仍须每张打分；若 score≥{FAST_SOFT_THRESHOLD} 且与上轮 Δ 很小可少重生，"
                f"但最终采纳默认仍要 ≥{threshold}（除非用户明确草稿/fast）。"
            )
        if ref_image:
            print(f"🖼️  垫图/参考图模式: {ref_image}")
            if ref_analysis:
                print(f"🔍 参考图解构基准: {ref_analysis}")
        print("\n👉 Agent：请将上方 Warm-Start prompt_block 完整并入第 1 轮 Prompt。可选 Best-of-N 首帧后进入 round。")
        return 0

    if not sf.exists():
        print("⚠️ 未找到进行中的收敛会话，正在自动初始化默认会话…")
        cmd_converge(
            root, data, "start",
            session_id=session_id, goal=goal or "自评收敛生图", module=module,
            ref_image=ref_image, ref_analysis=ref_analysis,
            threshold=threshold, max_rounds=max_rounds,
            converge_mode=converge_mode, draft_ok=draft_ok,
        )

    sess = json.loads(sf.read_text(encoding="utf-8"))
    th = float(sess.get("accept_threshold") or sess.get("threshold", DEFAULT_THRESHOLD))
    soft_th = FAST_SOFT_THRESHOLD if sess.get("fast_track") or sess.get("converge_mode") == "fast" else th
    mr = int(sess.get("max_rounds", DEFAULT_MAX_ROUNDS))
    rounds: list[dict[str, Any]] = sess.get("rounds") or []

    if action == "round":
        from improve import craft_lessons_from_round, print_round_lessons, ingest_term_to_knowledge

        r_no = round_num if round_num > 0 else (len(rounds) + 1)
        if r_no > mr:
            print(f"🛑 已超过最大轮次上限 ({mr} 轮)，请直接运行 `python3 pmem_art.py converge finish --apply` 结算最高分图。")
            return 1

        passed = float(score) >= th
        # Adaptive early-stop hint for fast track
        skip_ahead = False
        delta = None
        if rounds:
            prev = max(rounds, key=lambda x: x.get("round", 0))
            try:
                delta = abs(float(score) - float(prev.get("score", 0)))
            except (TypeError, ValueError):
                delta = None
        if (
            (sess.get("fast_track") or sess.get("converge_mode") == "fast")
            and float(score) >= soft_th
            and not passed
            and delta is not None
            and delta < 0.25
            and r_no >= 2
        ):
            skip_ahead = True

        lessons = craft_lessons_from_round(
            defects=defects, strengths=strengths, next_fix=next_fix,
            score=float(score), dims=dims,
        )
        sess.setdefault("lessons_all", []).extend(lessons)

        # knowledge from defects/fixes
        for blob in (defects, next_fix, strengths):
            if blob:
                ingest_term_to_knowledge(root, blob, source="converge_round")

        entry = {
            "round": r_no,
            "image": image,
            "score": round(float(score), 2),
            "dims": dims,
            "strengths": strengths or "构图与基础色调符合要求",
            "defects": defects or ("无明显硬伤，细节达标" if passed else "局部细节或光影仍需打磨"),
            "next_fix": ("已达标，无需继续叠加" if passed else (next_fix or "针对上述不合理处叠加负向词与结构约束")),
            "prompt": prompt,
            "passed": passed,
            "lessons": lessons,
            "skip_ahead_hint": skip_ahead,
            "recorded_at": _now_cst().strftime("%H:%M:%S"),
        }
        rounds = [r for r in rounds if r.get("round") != r_no]
        rounds.append(entry)
        rounds.sort(key=lambda x: x["round"])
        sess["rounds"] = rounds

        if passed:
            sess["status"] = "converged"
            sess["ActionRequired"] = "STOP_AND_FINISH"
            msg = f"✅ 第 {r_no} 轮得分 {score:.1f} >= {th}（合格达标）！请立即停止生图，运行 `python3 pmem_art.py converge finish --apply` 输出总表。"
        elif skip_ahead and sess.get("draft_ok"):
            sess["status"] = "fast_soft_accept"
            sess["ActionRequired"] = "STOP_AND_FINISH"
            msg = (
                f"⚡ Fast-track 草稿软达标：第 {r_no} 轮 {score:.1f} ≥ {soft_th} 且 Δ 很小。"
                f"用户已允许草稿 — 可 `converge finish --apply`；正式交付仍建议冲到 ≥{th}。"
            )
        elif r_no >= mr:
            best = max(rounds, key=lambda x: x["score"])
            sess["status"] = "max_rounds_reached"
            sess["ActionRequired"] = "STOP_PICK_BEST"
            msg = (
                f"🏁 第 {r_no}/{mr} 轮得分 {score:.1f} < {th}，已满 {mr} 轮上限！"
                f"全阶段最高分为第 {best['round']} 轮 ({best['score']:.1f} 分: {best['image']})。"
                f"请立即运行 `python3 pmem_art.py converge finish --apply` 输出汇总表。"
            )
        else:
            sess["status"] = "continue"
            sess["ActionRequired"] = f"GENERATE_ROUND_{r_no + 1}"
            msg = (
                f"🔄 第 {r_no}/{mr} 轮得分 {score:.1f} < {th}（不合格）。\n"
                f"   · 不合理处: {entry['defects']}\n"
                f"   · 下一轮叠加修正: {entry['next_fix']}\n"
            )
            if skip_ahead:
                msg += (
                    f"   · ⚡ Fast-track 提示：已 ≥{soft_th} 且与上轮变化很小 — "
                    f"可少做大重生、做局部修正；最终采纳仍要 ≥{th}（非草稿）。\n"
                )
            msg += f"   👉 请将修正策略叠加到 Prompt，继续生成第 {r_no + 1} 轮图片！"

        sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")
        print(msg)
        print_round_lessons(lessons, silent=silent)
        return 0

    if action in ("finish", "table", "status"):
        if not rounds:
            print("ℹ️ 当前收敛会话还没有轮次记录（先 round 再 status/finish）。")
            return 0

        accept_th = float(sess.get("accept_threshold") or th)
        if sess.get("draft_ok") and (sess.get("fast_track") or sess.get("converge_mode") == "fast"):
            accept_th = min(accept_th, FAST_SOFT_THRESHOLD)

        passing_rounds = [r for r in rounds if float(r.get("score", 0)) >= accept_th]
        if passing_rounds:
            winner = max(passing_rounds, key=lambda x: (x["score"], x["round"]))
            outcome_str = f"✅ **达标收敛**（第 {winner['round']} 轮达到 `{winner['score']:.1f} / 10.0` 分 ≥ `{accept_th}` 分合格线）"
        else:
            winner = max(rounds, key=lambda x: (x["score"], x["round"]))
            outcome_str = (
                f"⚠️ **满 {len(rounds)} 轮未达 `{accept_th}` 分，已自动挑选全阶段最高分**"
                f"（胜出：第 {winner['round']} 轮 `{winner['score']:.1f} / 10.0` 分）"
            )

        sess["winner"] = winner
        sess["status"] = "finished"
        sf.write_text(json.dumps(sess, ensure_ascii=False, indent=2), encoding="utf-8")

        warm = sess.get("warm_start") or {}
        md_lines = [
            f"### 🎯 自评收敛生图报告 — {sess.get('goal', '')}",
            "",
            f"- **目标模块**：`{sess.get('module')}`",
            f"- **收敛模式**：`{sess.get('converge_mode', 'quality')}`"
            + (" · ⚡ FAST-TRACK" if sess.get("fast_track") else ""),
            f"- **生图模式**：{'🖼️ 垫图解构收敛模式 (`' + sess.get('ref_image', '') + '`)' if sess.get('ref_image') else '✍️ 纯文本指令收敛模式'}",
        ]
        if warm.get("confidence") is not None:
            md_lines.append(f"- **Warm-Start 置信度**：`{warm.get('confidence')}`")
        if sess.get("ref_analysis"):
            md_lines.append(f"- **参考图解构基准**：{sess.get('ref_analysis')}")
        md_lines.extend([
            f"- **收敛结论**：{outcome_str}",
            f"- **最终采用图片**：`{winner.get('image')}`（综合评分 **`{winner.get('score'):.1f}`**）",
            "",
            "#### 📊 全阶段生图迭代评分与优劣分析总表",
            "",
            "| 轮次 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |",
            "| :---: | :--- | :---: | :--- | :--- | :--- | :---: |",
        ])

        for r in rounds:
            is_win = (r["round"] == winner["round"])
            badge = "🏆 **胜出采用**" if is_win else ("✅ 达标" if r.get("passed") else "❌ 未达标")
            score_cell = f"**{r['score']:.1f}**" + (f"<br><small>{r['dims']}</small>" if r.get("dims") else "")
            img_cell = f"`{r.get('image') or '-'}`"
            md_lines.append(
                f"| 第 {r['round']} 轮 | {img_cell} | {score_cell} | {r.get('strengths', '-')} | {r.get('defects', '-')} | {r.get('next_fix', '-')} | {badge} |"
            )

        md_lines.append("")
        # 本轮可学 aggregate
        all_lessons = []
        for r in rounds:
            all_lessons.extend(r.get("lessons") or [])
        if not all_lessons:
            all_lessons = sess.get("lessons_all") or []
        if all_lessons:
            md_lines.append("#### 📚 本轮可学（能力提升）")
            md_lines.append("")
            seen = set()
            for L in all_lessons:
                key = (L.get("category"), L.get("lesson"))
                if key in seen:
                    continue
                seen.add(key)
                md_lines.append(f"- **[{L.get('category')}]** {L.get('lesson')} → _{L.get('drill')}_")
            md_lines.append("")

        if not passing_rounds:
            md_lines.append(
                f"> 💡 **阶段总结**：本次共迭代 {len(rounds)} 轮，最高分为第 {winner['round']} 轮（`{winner['score']:.1f}` 分），"
                f"仍留有轻微不足：「{winner.get('defects')}」，后续可针对该点微调或局部重绘。"
            )

        saved_paths: list[str] = []
        reflection_path = None
        tip = None
        if action == "finish" and apply_memory:
            from feedback import write_memory_entry
            from improve import write_session_reflection

            mod = sess.get("module") or "brand.GlobalStyle"
            def _ensure_conv_asset(img_str: str, m_id: str, prompt_str: str) -> str:
                if not img_str:
                    return ""
                import shutil
                cand = Path(img_str)
                if not cand.is_absolute():
                    cand = root / img_str
                if not cand.is_file():
                    return img_str
                try:
                    rel_c = cand.resolve().relative_to(root.resolve()).as_posix()
                    if rel_c.startswith("assets/"):
                        return rel_c
                except Exception:
                    pass
                dom = m_id.split(".")[0] if "." in m_id else "misc"
                ent = m_id.split(".")[1].lower() if "." in m_id else "general"
                dest_rel = f"assets/{dom}/{ent}/{cand.name}"
                dest_p = root / dest_rel
                dest_p.parent.mkdir(parents=True, exist_ok=True)
                if cand.resolve() != dest_p.resolve():
                    shutil.copy2(str(cand), str(dest_p))
                try:
                    from classify import classify_asset, ensure_module_from_classification
                    cl = classify_asset(root, data, path=dest_rel, prompt=prompt_str)
                    cl["suggested_module"] = m_id
                    cl["domain"] = dom
                    cl["entity"] = m_id.split(".")[1] if "." in m_id else m_id
                    cl["canonical_rel"] = dest_rel
                    ensure_module_from_classification(root, data, cl, force_active=True)
                except Exception:
                    pass
                return dest_rel

            win_img = _ensure_conv_asset(
                winner.get("image", ""),
                mod,
                str(winner.get("prompt") or sess.get("goal") or ""),
            )
            if win_img:
                winner["image"] = win_img

            win_summary = f"[收敛胜出 {winner['score']:.1f}分] {sess.get('goal', '')[:50]} — {winner.get('strengths', '')[:30]}"
            win_caption = (
                f"🏆 收敛胜出定稿 ({winner['score']:.1f}/10分 · 第{winner['round']}轮)："
                f"{sess.get('goal', '')}"
                + (f" · 亮点：{winner.get('strengths')}" if winner.get("strengths") else "")
            )
            win_body = (
                f"**【闭环收敛胜出定稿（第 {winner['round']}/{len(rounds)} 轮 · {winner['score']:.1f} 分）】**\n"
                f"- **生成目标**：{sess.get('goal')}\n"
                f"- **收敛模式**：{sess.get('converge_mode')}{' · fast-track' if sess.get('fast_track') else ''}\n"
                f"- **保留原因（亮点）**：{winner.get('strengths')}\n"
                f"- **最终使用 Prompt**：`{winner.get('prompt') or sess.get('goal')}`\n"
            )
            if sess.get("ref_image"):
                win_body += f"- **参考垫图**：`{sess.get('ref_image')}`（解构：{sess.get('ref_analysis')}）\n"
            if warm.get("prompt_block"):
                win_body += f"\n<details><summary>Warm-Start 包</summary>\n\n```\n{warm.get('prompt_block')}\n```\n</details>\n"
            p_rec = write_memory_entry(
                root,
                module=mod,
                kind="recipe",
                summary=win_summary,
                body=win_body,
                asset=win_img,
                role="approved",
                caption=win_caption,
                extra_meta={
                    "ai_params": {
                        "prompt": str(winner.get("prompt") or sess.get("goal") or ""),
                        "score": winner.get("score"),
                        "round": winner.get("round"),
                        "dims": winner.get("dims", ""),
                    }
                },
            )
            saved_paths.append(str(p_rec.relative_to(root)))

            failed = [r for r in rounds if not r.get("passed") and r.get("defects")]
            if failed:
                worst = min(failed, key=lambda x: x["score"])
                worst_img = _ensure_conv_asset(
                    worst.get("image", ""),
                    mod,
                    str(worst.get("prompt") or sess.get("goal") or ""),
                )
                red_summary = f"[收敛踩坑红线] {sess.get('goal', '')[:30]}：避免「{worst.get('defects', '')[:45]}」"
                red_caption = (
                    f"❌ 第{worst['round']}轮收敛打回 ({worst['score']:.1f}分)："
                    f"{worst.get('defects', '')} → 修正：{worst.get('next_fix', '')}"
                )
                defect_bullets = "\n".join(
                    f"- 第 {r['round']} 轮 ({r['score']:.1f}分) 不合理处：{r['defects']} → 修正：{r['next_fix']}"
                    for r in failed
                )
                red_body = (
                    f"**【迭代过程中暴露的不合理项（下次生图直接规避）】**\n\n"
                    f"{defect_bullets}\n"
                )
                p_red = write_memory_entry(
                    root,
                    module=mod,
                    kind="style_redline",
                    summary=red_summary,
                    body=red_body,
                    asset=worst_img,
                    role="rejected",
                    caption=red_caption,
                )
                saved_paths.append(str(p_red.relative_to(root)))

            # Session reflection for continuous self-improve
            sess["lessons_all"] = all_lessons
            reflection_path = write_session_reflection(root, sess, winner=winner, outcome=outcome_str)
            try:
                import json as _json
                ref_data = _json.loads(reflection_path.read_text(encoding="utf-8"))
                ref_data["lessons"] = all_lessons[:12]
                reflection_path.write_text(_json.dumps(ref_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except Exception:
                pass
            saved_paths.append(str(reflection_path.relative_to(root)))

            md_lines.append("")
            md_lines.append("#### 🧠 已自动沉淀至 `.memory-art` 的记忆条目")
            for sp in saved_paths:
                md_lines.append(f"- `{sp}`")
            md_lines.append("")
            md_lines.append(
                "> 🔇 静默自动驾驶已跑完（反思 + taste + learn 队列）。"
                "进阶 peek：`improve run` · `coach` · `learn suggest` · `progress`；全量本表加 `--verbose`。"
            )

            try:
                from improve import run_silent_autopilot
                auto = run_silent_autopilot(
                    root,
                    data,
                    session_id=session_id,
                    lessons=all_lessons,
                    defects=str(winner.get("defects") or ""),
                    strengths=str(winner.get("strengths") or ""),
                    winner=winner,
                    rounds=rounds,
                    source="converge_finish",
                )
                tip = auto.get("tip")
            except Exception as ex:
                tip = None
                if verbose:
                    print(f"⚠️ autopilot 跳过: {ex}")

        if action == "finish" and apply_memory:
            try:
                from pmem_art import refresh_atlas_silent
                refresh_atlas_silent(root)
            except Exception:
                pass
        report_text = "\n".join(md_lines)
        report_file = root / ".memory-art" / "converge" / f"{session_id}_report.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        report_file.write_text(report_text + "\n", encoding="utf-8")

        # Default: whisper UX. table/status or --verbose: full Markdown.
        want_full = (not silent) or action in ("table", "status") or verbose
        if action == "finish" and silent and not verbose:
            badge = "✅" if passing_rounds else "🏆"
            print(
                f"{badge} 收敛完成 · 第 {winner.get('round')} 轮 "
                f"{float(winner.get('score', 0)):.1f}/10 · `{winner.get('image')}`"
            )
            if tip:
                from improve import print_whisper_tip
                print_whisper_tip(tip)
            elif not apply_memory:
                print("（未 --apply，跳过静默沉淀）")
            print(f"📎 全量报告: {report_file.relative_to(root)} （加 --verbose 打印）")
        else:
            print(report_text)
            if tip and action == "finish":
                from improve import print_whisper_tip
                print_whisper_tip(tip)
        return 0

    if action == "warm":
        # standalone warm-start preview without starting session
        from improve import build_warm_start_pack, print_warm_start
        mod = module
        if not mod and goal:
            from feedback import infer_module_from_text
            mod = infer_module_from_text(goal, data)
        pack = build_warm_start_pack(root, data, module=mod or "brand.GlobalStyle", goal=goal or "")
        print_warm_start(pack)
        return 0

    print(f"未知 converge 子操作: {action}")
    return 1
