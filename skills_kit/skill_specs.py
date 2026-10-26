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
        "alias": "art-draw",
        "title": "【强制8轮≥9.6收敛】通用生图（纯文本/垫图 · 打分挑刺 · 评分履历可见）",
        "description": (
            "当用户输入 /pmem-draw 或 /art-draw（如「/pmem-draw 生成一张xxx风格的xxx图」或「/pmem-draw [附带一张图] 生成一张xxx图」）时触发。"
            "执行「先查记忆/分析参考图 → 生成1张图 → 严苛五维自评打分+指出不合理处 → 未达9.6分则叠加修正继续生图（最多8轮）→ "
            "达标或满8轮挑最高分 → 默认展示每轮评分/不足/改点并沉淀记忆（只要终稿加 `--quiet`）」的完整闭环。"
        ),
        "body": r"""# `/pmem-draw`（别名 `/art-draw`）— 8轮 9.6分 闭环自评收敛生图技能

你现在运行在 **pmem-art 闭环自评收敛生图模式**。无论是纯文字生图还是用户丢入了一张参考图，你都必须严格执行以下闭环流程，**绝不能只生一张图就草草交差**（除非第 1 轮真实严苛评分就达到 `>= 9.6`）。

---

## 一、支持两种触发方式

### 方式 A：纯文本指令生图
> 例：`/pmem-draw 生成一张东方青瓷水彩风格的阿斯特拉半身立绘`
- 直接进入 **Step 1（召回记忆）→ Step 2（最多8轮自评收敛循环）→ Step 3（展示评分履历 + 静默沉淀记忆）**。

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
   python3 pmem_art.py converge start --goal "<用户目标描述>" --module <目标模块> [--mode quality|fast] [--scale low|medium|high|recompose] [--recompose-dir "<新构图方向>"] [--ref-image <参考图>] [--ref-analysis "<参考图分析>"]
   ```
   - 默认 `--mode quality` = 完整 8×≥9.6。
   - `--scale`：`low` 贴原修瑕 · `medium` 小优化锁机位（默认）· `high` 大胆跃升+可叙事 · `recompose` 须配 `--recompose-dir`。
   - `--mode fast`：warm-start 置信度高时可走 **fast track**（仍须每张打分；最终采纳默认仍要 ≥9.6，除非用户明确说「草稿/fast/先看看」）。
   - 把打印出的 **Warm-Start `prompt_block` 完整并入第 1 轮 Prompt**。
   - **档位保留集（V4 短骨架；禁止全档复读肯定锁）**：
     - `low`：姿态/机位锁 **一条即可**；goal ≤20% 修瑕。
     - `medium`：goal **~40%**；锁机位；可小幅姿态/局部布局；骨架「保画风与机位，小幅姿态/局部布局；柔化光影…」。
     - `high`：goal **≤80%**；`allow_recompose` + 可改元素数；forbid=`no_identity_swap`；骨架「保媒介与身份，提升光影张力；可加风格内叙事点缀」；**≥2 轮才停**。
     - `recompose`：目标机位 = `--recompose-dir`；骨架「保画风色板，按「方向」重构机位」；**≥2 轮**；未换机位勿停；与 bold 拆开。
   - **最优方向按档分流**（加法，不是第二份锁）。出图前可跑：`python3 pmem_art.py check-scale-gates --self-check`。
3. **可选 Best-of-N 首帧**：第 1 轮先构思 2~3 个方向（或并行想法），挑最佳进入后续 converge（在回复里写明选了哪条）。

---

### Step 2：闭环自评收敛循环（最多 8 轮，合格线 `>= 9.6 / 10.0`）

令轮次 $i = 1, 2, \dots, 8$：

#### 2.1 生成第 $i$ 轮单张候选图
- **第 1 轮**：用用户目标、参考图（若有）和红线写完整提示词，垫图用最初那张参考图。
- **第 2 轮起**：出图前先跑 `python3 pmem_art.py converge next --id <id>`，或直接用上一轮审图印出的「下一轮先垫这张」。生图参考图只用这张最高分成图，比它差的一轮不垫。提示词用它印出的那一句，只改没过的那一处。不要再把最初的原图垫进去，也不要把前几轮的修正叠进同一段。
- 调用生图工具（如 `GenerateImage`）**生成 1 张图**。参考图路径用 `converge next` 给出的那张。提示词写明：只改点名的那一处，没点名的地方保持垫图。画完再 `converge generate` 登记。

#### 2.2 严苛审图与五维打分（每维满分 10，再按档位权重合成）
生成后**亲自看图**按 Absolute-5D 打分（有结构、透视、质感硬伤就必须压到 9 以下）。有独立 VLM Key 时 API 主分；**无 Key 时仍由你（本模型）按检查表看图评分**，门槛照旧 `>=9.6`，未达标继续，满 8 轮取最高分——**禁止**用像素离线尺另设 8.50 早停。可参考 `skills_kit/absolute_5d_agent_rubric.py` 的 `agent_absolute_5d_judge_prompt()`。
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
- **情况 1：本轮评分 `>= 9.6` 且已满本档 `min_rounds_before_stop`（`high`/`recompose` 默认 ≥2 轮）**
  🎉 **合格达标！** 结束生图循环，以第 $i$ 轮为胜出图，进入 Step 3。
- **情况 1b：分数够但未满最小轮次** → 视为未停机。下一轮垫目前最高分的那张，只补还没到位的那一处，不按优选方向重画整张。
- **情况 2：本轮评分 `< 9.6` 且 $i < 8$**
  🔄 **不合格！** 下一轮垫目前分数最高的那张，只把那张没过的地方写成一句。本轮更低分，就不拿本轮接着垫。**立即继续生第 $i+1$ 张图**。
- **情况 3：已满 8 轮（$i = 8$）且评分仍 `< 9.6`**
  🏁 **达到 8 轮上限，停止循环！** 从第 1 ~ 8 轮中**挑选综合评分最高的那一轮图片**作为最终交付图，进入 Step 3。

---

### Step 3：结算最优图 & 自动沉淀记忆（默认展示评分履历；记忆写入仍静默）

循环结束后，运行：
```bash
python3 pmem_art.py converge finish
```
该命令会自动：
1. 选出达标轮次（`>= 9.6`）或全阶段最高分轮次（`Best of 8`）。
2. 将最终胜出图通过 `ingest` / `feedback` 写入 `.memory-art` 的 `recipe`（正向定稿锚点），并把迭代过程中暴露的典型不合理点写入 `style_redline` / `visual_correction`。
3. 生成并**默认打印**标准 Markdown 评分履历表（只要一行结论时加 `--quiet`）。

**对用户的默认展示（评分履历可见 · 记忆写入静默）：**
每轮 `converge judge` 之后，**必须**在对话里展示本轮审图卡（用户明确说「安静/quiet」或 CLI `--quiet` 才可省略）：
1. 本轮图（或路径）
2. **五维分 + 综合分**（例：`构图8.6/光影8.2/透视7.8/质感8.0/风格8.4 · 总分 8.40`）
3. **不合理 / 不足**（`defects`，具体到部位）
4. **下一轮主要改哪里**（`next_fix`）；若已达标则写「定稿」
循环结束后再展示：🏆 **最终胜出图** + 全轮次评分总表（分数 / 不足 / 改点 / 结果）。
报告**最底部**必须带档位合同脚注（`converge finish` 已打印），原样转述，例如：
> **目前是 LOW 档**… 若画师说「构图松一点」，表上该维显示 **`75%（默认95%，-20%）`**（档位仍是 low，只微调这一维）。
画师可写：`构图松一点` / `光影锁定降到 40%` / `升到 medium`；Agent 应跑 `converge lock --lock-text "…"` 再继续生图。
💡 若 CLI 打出一行「小提示」，原样转述（每会话最多 1 条）。
**禁止**旁白「正在写反思 / 更新 taste / 入队 learn / 沉淀红线」——记忆仍在 `finish` 后台静默完成。
improve/coach/learn 推销仅在用户主动要时再给。

### Agent 后台（对用户不可见）
`finish`（默认写记忆；`--no-apply` 可跳过） 已自动：写 recipe/红线 + 会话反思 + `run_silent_autopilot`（更新 taste、强化配方、悄悄 enqueue 1–2 条 learn 建议）。

### 闭环总览
`装上就用 → 画 → 每轮摊开评分与改点 → 偶发一行小提示 → 记忆后台变强；只要终稿用 --quiet；进阶 peek：improve/coach/learn/progress`
## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-improve` / `/pmem-learn`。
- 对用户默认展示：**每轮审图卡 + 胜出图 + 全轮评分履历**；记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看教练/广度再用 `/pmem-improve`·`/pmem-coach`·`progress`。
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
2. **五维打分与挑刺（Absolute-5D，与 `converge judge` 同一套标签）**：
   - 每维满分 10，写入格式：`构图x/光影x/透视x/质感x/风格x`（例：`构图8.6/光影8.2/透视7.8/质感8.0/风格8.4`）。
   - UI/App Icon 专用标签仅在对应资产上使用；**禁止**再手填旧加和尺「风格2.5/结构2.5/…」当主报告（旧串仍可被解析，但新审稿一律 Absolute-5D）。
   - 明确列出 **✅ 合理亮点** 与 **❌ 不合理/需返修点**，并给出可直接用于下一轮重绘的 **修正 Prompt 建议**。
3. **自动沉淀红线**：
   - 若评分 `< 9.6` 或用户认可某条挑刺结论，调用 `python3 pmem_art.py feedback "<具体不合理点>" --module <模块> --asset <图片路径>` 自动写入记忆库。
4. **展示与静默边界**：默认必须向用户展示 Absolute-5D 分数卡 + ✅/❌ 要点 + 修正 Prompt；记忆写入仍勿旁白。完整 `/pmem-coach` 练习计划仅当用户明确要教练或 `--verbose` 时再展开；CLI 若打出一行「小提示」可原样转述（每会话最多 1 条）。
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
   - 按 9.6 分标准生成与自评，完成后运行 `python3 pmem_art.py ingest <新图路径> -p "<含角色名+画风/差分词的Prompt>" --apply` 自动创建子模块并归位。
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
        "title": "【强制8轮≥9.6收敛】SpriteCook式 UI Kit/HUD/九宫格整套",
        "description": (
            "【截图可见·必读】/pmem-ui 与 /art-ui 生成 UI Kit/HUD 时，概念稿与关键组件均强制「最多8轮、合格线≥9.6」闭环自评收敛（生1张→打分挑刺→展示不足与改点→<9.6叠加修正→满8轮挑最高分→评分履历可见）。"
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
1. `search` 召回 `ui.*` 红线与定稿 → 2. **概念先行** → 3. 透明组件表 → 4. 九宫格 + 状态族 → 5. **强制 8轮 ≥9.6**（每轮展示评分履历） → `finish` 打印履历 + **记忆静默写入**（勿旁白记忆）

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
2. 若无概念图：先生成 **1 张完整屏幕概念稿**（整屏布局，统一材质与色板），用 `/pmem-draw` 同款 **8轮 >=9.6 收敛** 打磨概念稿：
   ```bash
   python3 pmem_art.py converge start --goal "UI概念稿：<屏幕类型+风格>" --module <ui.模块> [--scale medium|high]
   # 每轮：converge generate 生图，再 Absolute-5D converge judge（有 Key→API；无 Key→本模型检查表；禁止像素尺 8.50 早停）
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

### Step 4：关键件二次收敛（概念稿已强制；核心件不达标则继续）
对主面板、主按钮等核心件，若 Absolute-5D 评分 `< 9.6`（重点查：中心拉伸区是否干净、转角是否形变、透明底毛边、状态族是否同系），继续 `converge generate` / `converge judge` 直到达标或满 8 轮（门槛仍 9.6，禁止像素 8.50 早停）。

### Step 5：沉淀记忆
```bash
python3 pmem_art.py ingest <concept或主面板路径> -p "UI kit <屏幕> 概念/主面板" --apply
python3 pmem_art.py feedback "UI套件色板与九宫格规范：<摘要>" --module <ui.模块> --kind art_decision
```

## 三、UI 专用五维评分侧重（满分 10.0，`>= 9.6` 合格）
`--dims` 优先写 **UI 专用 Absolute 标签**（每维 0–10，由 `parse_5d_dims` 按 UI 权重合成），示例：
`风格色板契合9.5/九宫格合理性9.2/光影材质9.0/红线合规8.8/套件一致性9.1`
侧重含义：
1. 风格色板契合 — 与概念稿同材质同色板
2. 九宫格合理性 — 中心区干净、角不糊、可拉伸
3. 光影材质 — 完成度
4. 红线合规 — RGBA 透明底、分辨率、无脏边
5. 套件一致性 — normal/pressed 等同系，不「各画各的」
（旧加和小数写法如 `风格2.5/九宫格2.4/…` 仍兼容；无 UI 关键词时也可用通用 `构图/光影/透视/质感/风格`。）

## 四、最终交付必须包含
1. 概念稿 + 组件表 + `elements/` + `manifest.json`（含九宫格）
2. 若跑了收敛：默认附上全轮次评分优劣总表（不足/改点）；只要终稿用 `--quiet`
3. 已写入 `.memory-art` 的 recipe / redline 路径


## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
""",
    },
    {
        "name": "pmem-concept",
        "alias": "art-concept",
        "title": "【强制8轮≥9.6收敛】原画/概念图/Key Art（ZHO·FLUX式完整句Prompt）",
        "description": (
            "【截图可见·必读】/pmem-concept 与 /art-concept（原画/概念图/Key Art）与 /pmem-draw 一样，强制执行「最多8轮、合格线≥9.6分」闭环自评收敛："
            "生1张→五维打分+指出不合理处→展示不足与改点→<9.6则叠加修正继续生→达标即停或满8轮挑最高分→默认展示评分履历并沉淀记忆。"
            "触发例：「/pmem-concept 画一张青瓷废土主视觉Key Art」「/art-concept [附参考] 同氛围气氛图」。"
            "Prompt 采用 ZHO/Yolain/Comfy-FLUX 式完整自然语言句（主体靠前、正向写排斥项）。"
        ),
        "body": r"""# `/pmem-concept`（别名 `/art-concept`）— 原画 / 概念图 / Key Art

> ⚠️ **【强制闭环 · 与 `/pmem-draw` 同等】**  
> 本技能生成原画/概念图/Key Art 时，**必须**跑满同一套收敛规则：  
> **最多 8 轮生图 · 合格线 `≥ 9.6 / 10.0` · 未达标叠加修正继续生 · 满 8 轮挑全阶段最高分 · 每轮展示评分/不足/改点 · `finish` 默认打印履历并写记忆（`--quiet` 只要终稿）**。  
> **禁止只生一张图就交差**（除非第 1 轮真实严苛评分就 ≥ 9.6）。

## 怎么用（复制即用）
```text
/pmem-concept 画一张东方青瓷废土的主视觉 Key Art，宽幅海报，电影感侧逆光
/art-concept 生成一张浮空遗迹黄昏气氛概念图，青瓷白+墨蓝+鎏金
/pmem-concept [拖入参考图] 保持构图与色板，画一张同世界观角色登场 Key Art
```

## 原理（截图摘要）
1. **Warm-Start + 与 draw 同等 8×≥9.6** → 2. `search`/口味召回 → 3. **FLUX 完整句** → 4. 垫图解构 → 5. `converge`（每轮摊开评分履历） → 6. `finish` 打印履历 + 记忆静默写入

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
python3 pmem_art.py converge start --goal "<概念图目标>" --module <模块> [--scale low|medium|high|recompose] [--recompose-dir "…"] [--ref-image …] [--ref-analysis …]
```

### Step 2：最多 8 轮自评收敛（合格线 `>= 9.6`）
每轮：
1. 垫目前分数最高的那张成图。只把那张没过的那一处写成一句，不重写整段，也不把前几轮的修正叠在一起。比它差的一轮不接着垫。
2. 生成 **1 张** 概念图 / Key Art。
3. **Absolute-5D** 严苛打分（有 Key→API；无 Key→本模型检查表；**禁止**像素尺 8.50 早停）+ 说出合理处与不合理处 → `converge generate` 然后 `converge judge`。
4. `>= 9.6` 立即停；`< 9.6` 且未满 8 轮则继续；满 8 轮挑最高分。

**概念图五维侧重（`--dims` 必须可被 `parse_5d_dims` 解析，否则本轮记 0 分）**：
主用 Absolute-5D：`构图x/光影x/透视x/质感x/风格x`（每维 0–10）。
评判侧重：构图→叙事机位与层次；光影→电影感侧逆/体积光；透视→空间纵深；质感→空气介质与材质可读；风格→色板与 Key Art 完成度。
示例：`--dims "构图9.2/光影9.0/透视8.8/质感8.9/风格9.1"`。
旧侧重串（`风格色板/构图叙事与透视/光影材质/红线合规/氛围意图还原`）现仍可解析为兼容加和尺，但**新会话请统一写 Absolute-5D**，以便与 `/pmem-draw` 履历直接对比。

### Step 3：结算与沉淀
```bash
python3 pmem_art.py converge finish
```
向用户默认展示：每轮审图卡（五维分/不足/改点）+ 胜出图 + 全轮评分履历；只要终稿时用 `--quiet`。

## 四、与 `/pmem-draw` 的分工
- **`/pmem-draw`**：通用单图收敛（角色立绘、道具、单件 UI 等）
- **`/pmem-concept`**：专门服务 **概念图 / Key Art / 气氛图**，强制 FLUX 式完整句 Prompt 与叙事构图标准


## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
""",
    },
    {
        "name": "pmem-icon",
        "alias": "art-icon",
        "title": "【强制8轮≥9.6收敛】iOS/Android App Icon 应用图标母版 + jezweb式一致化 SVG 图标集 + 游戏道具栅格图标",
        "description": (
            "【截图可见·必读】/pmem-icon 与 /art-icon 支持三大模式：(A) iOS/Android 1024×1024 App Icon 桌面启动图标母版（满幅直角出图+72%~80%圆角安全区+多尺寸导出矩阵+深浅色自适应）；"
            "(B) jezweb 式一致化 SVG 矢量图标集；(C) 游戏道具 64/128/256px 透明底栅格图标。"
            "全部支持 converge generate 与 converge judge 两步分离，以及动态阈值收敛闭环。"
        ),
        "body": r"""# `/pmem-icon`（别名 `/art-icon`）— jezweb 式一致化图标集 / SVG 取向生成

## 怎么用（复制即用）
```text
/pmem-icon 给本项目做一套 24px Clean 预设导航+背包图标（SVG），输出 style-spec 与 preview.html
/art-icon home settings inventory craft map quest
/pmem-icon [拖入品牌样张] 按这个线宽与圆角补齐：phone email location
```

## 原理（截图摘要）
1. 先锁 **style-spec** → 2. SVG 硬规则 → 3. 分批生成 → 4. 交付 preview → 5. 关键枚 **Warm-Start + 8×≥9.6** → 6. 反思 / improve / learn 扩图标技法卡

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

### Step 5：关键图标 8轮≥9.6 收敛（App Icon 母版强制；SVG/道具集：点名或一致性失败时强制）
整集批量生成不必对每枚跑满 8 轮；**App Icon 1024 母版**、用户点名「不对」、或一致性审查不通过的关键枚必须跑满 Absolute-5D 闭环（有 Key→API；无 Key→本模型；禁止像素 8.50 早停）：
```bash
python3 pmem_art.py converge start --goal "图标 <name> 对齐 style-spec" --module brand.WorldStyle
# 生成 → Absolute-5D 自评 → converge generate / converge judge → finish
```

### Step 6：沉淀
```bash
python3 pmem_art.py feedback "图标集 style-spec：<preset+stroke+grid摘要>" --module brand.WorldStyle --kind art_decision
python3 pmem_art.py ingest icons/preview.html -p "icon set preview" --apply   # 若适用
```

## 二之二、App Icon 模式（iOS App Store / Android Adaptive 1024×1024 桌面应用图标专项）

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
- `converge finish` 后系统自动写反思/口味/learn 队列——**无需**再跑 `/pmem-improve`。
- 对用户默认展示：**每轮五维分 + 不足 + 改点 + 胜出图 + 全轮履历**；若有「小提示」原样转述（每会话最多 1 条）。**禁止**旁白记忆写入。
- 只要终稿：`--quiet`。教练 / 广度：用户明确要求或进阶技能时再给。
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
`finish`（默认写记忆；`--no-apply` 可跳过） → 反思 JSON + silent autopilot → taste.json；本技能只是把后台已经做过的事**大声读一遍**。

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
    {
        "name": "pmem-merge-ladder",
        "alias": "art-merge",
        "title": "同域合成梯（先过关系，再逐张抬美术）",
        "description": (
            "当用户输入 /pmem-merge-ladder 或 /art-merge，或要一条同域合成升级梯时触发。"
            "分两段，各最多 8 轮。第一段先在文字上定稿八件的合成关系，不看美术品质，过了再每一档单独出一张正方形核对。"
            "关系过关后，第二段在这些正方形上抬光影和质感，合格线 ≥ 9.6。"
            "风格优先用用户写下的；没写就用放进来的参考图；都没有再用默认「质感好的卡通可爱」。"
            "每一件单独放在一个同样大的正方形里，不把八件画进同一张。两件相同的这一档合成下一档。相邻档只大一点，低档也要占满格子大半。"
            "件数、顺序和档位锁着。关系散了，美术分再高也不算过。"
        ),
        "body": r"""# `/pmem-merge-ladder`（别名 `/art-merge`）— 同域合成梯

分两段。第一段只把八件的合成关系排对。第二段在这些过关的正方形上把画面画好。两段都过，才交付。

## 风格

第二段的风格按这个顺序取，只取一条：
1. 用户写下了风格，就用写下的风格。
2. 没写风格，但放了参考图，就用这张参考图的风格。不抄参考图里的物件。先跑 `python3 pmem_art.py ref-read <参考图路径>`。底是透明的，不要写成黑底。表面用看见图上的那一句，整组每一张、后面每一轮都用这同一句，不换成另一种媒介。小高光不要写成油亮。表面光洁，也不要改成毛毡或纸纹。不要把参考图文件垫进生图。第一张比参考图更油、更黑或更毛，就改这几个词再出。表面那一句已经对了，就留着。
3. 风格和参考图都没有，用默认的质感好的卡通可爱。

## 第一段 · 合成关系

先不出图。只在文字上定八件的顺序，不看质感、光影和风格，不用美术 9.6 决定停不停。最多改 8 稿。

过关要同时满足：正好八件。每一件单独占一个正方形，八个格子一样大，不把八件画进同一张。画面里只有这一件，居中。两件相同的这一档合成下一档，所以每一档仍然是一件，不是一对，也不是一组场景。低档只比高档小一圈，相邻档的大小差要小：最低档也要占到正方形的大半，最高档留一圈边，不顶出格子，也不能缩成格子中间的一个小点。沿档位零件变多或剪影更复杂。末档最大、零件最多，仍然是一件。相邻两档的剪影家族不能相同。

每一稿写成八行。每行写：第几档、物件、剪影家族、比上一档大多少、比上一档多了什么零件。这一稿先交给独立文本模型，只谈这八行的关系，不谈美术。请它按上面六条判断过没过，并指出没过的是哪一行。指定的模型连不上，就改用当前默认模型，按同样六条判断，可以定稿。有模型回了「定稿」才出图。没过只改它指出的那几行，已经过的行留下。不写「不要画某件」。最多改 8 稿。

它判六条都过了，才算定稿，然后每一档单独出一张正方形。对不上，就改那一档的这一张，不重新选八件。像素也对上，才进入第二段。8 稿文字仍过不了，就停在这一段，不进入第二段。

## 第二段 · 美术品质

只从第一段过关的那些正方形接着画，不重选八件。每一档仍是单独一张正方形。最多再 8 轮，合格线 ≥ 9.6。这一段用 medium 档。表面那一句每轮原样保留，改动只写在没过的那一格上。生图那一句不写光影张力、体积光、次表面散射。正方形、一件一格、件数、顺序、档位大小继续锁着：不把八件拼进同一张，不把低档缩得很小，不增删件数，不重排。

每轮先出图，再看像素。向用户写出五维分、不足、下一轮改点，并再查一遍第一段的合成关系。关系还在、美术分 ≥ 9.6，才停。关系散了，这一轮美术分再高也不算过，下一轮回到过关稿的件数、顺序和档位上改质感。满 8 轮还没有两段都过的，留下美术最高且关系仍在的那些正方形；关系都不在了，就交付第一段那些过关的正方形。

用 `converge generate` 记生图，`converge judge` 记审图，结束时 `converge finish`。第二段的 `converge start` 用 `--scale medium`。
""",
    },
]



