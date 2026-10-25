---
name: pmem-draw
description: 当用户输入 /pmem-draw 或 /art-draw（如「/pmem-draw 生成一张xxx风格的xxx图」或「/pmem-draw [附带一张图] 生成一张xxx图」）时触发。执行「先查记忆/分析参考图 → 生成1张图 → 严苛五维自评打分+指出不合理处 → 未达9.6分则叠加修正继续生图（最多8轮）→ 达标或满8轮挑最高分 → 默认静默结算并沉淀记忆（`--verbose` 才倾倒全轮次评分表）」的完整闭环。
---

# `/pmem-draw`（别名 `/art-draw`）— 8轮 9.6分 闭环自评收敛生图技能

你现在运行在 **pmem-art 闭环自评收敛生图模式**。无论是纯文字生图还是用户丢入了一张参考图，你都必须严格执行以下闭环流程，**绝不能只生一张图就草草交差**（除非第 1 轮真实严苛评分就达到 `>= 9.6`）。

---

## 一、支持两种触发方式

### 方式 A：纯文本指令生图
> 例：`/pmem-draw 生成一张东方青瓷水彩风格的阿斯特拉半身立绘`
- 直接进入 **Step 1（召回记忆）→ Step 2（最多8轮自评收敛循环）→ Step 3（静默结算与沉淀记忆）**。

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
   - `--scale`：`low` 贴原修瑕 · `medium` 补足（默认）· `high` 允许戏剧光影升级 · `recompose` 须配 `--recompose-dir`。
   - `--mode fast`：warm-start 置信度高时可走 **fast track**（仍须每张打分；最终采纳默认仍要 ≥9.6，除非用户明确说「草稿/fast/先看看」）。
   - 把打印出的 **Warm-Start `prompt_block` 完整并入第 1 轮 Prompt**。
   - **档位保留集（V4 短骨架；禁止全档复读肯定锁）**：
     - `low`：姿态/机位锁 **一条即可**；goal ≤20% 修瑕。
     - `medium`：goal **25%–45%**；指令骨架「保画风与主体，柔化光影…」。
     - `high`：goal **50%–80%**；骨架「保媒介与身份，提升光影张力」；**≥2 轮才停**。
     - `recompose`：目标机位 = `--recompose-dir`；骨架「保画风色板，按「方向」重构机位」；**≥2 轮**；未换机位勿停。
   - **最优方向按档分流**（加法，不是第二份锁）。出图前可跑：`python3 pmem_art.py check-scale-gates --self-check`。
3. **可选 Best-of-N 首帧**：第 1 轮先构思 2~3 个方向（或并行想法），挑最佳进入后续 converge（在回复里写明选了哪条）。

---

### Step 2：闭环自评收敛循环（最多 8 轮，合格线 `>= 9.6 / 10.0`）

令轮次 $i = 1, 2, \dots, 8$：

#### 2.1 生成第 $i$ 轮单张候选图
- 综合「用户原始需求 + 参考图解构特征（若有）+ `.memory-art` 历史红线 + **前 $i-1$ 轮累积的修正指令**」，构造第 $i$ 轮生图 Prompt。
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

#### 2.4 收敛判定（核心规则！）
- **情况 1：本轮评分 `>= 9.6` 且已满本档 `min_rounds_before_stop`（`high`/`recompose` 默认 ≥2 轮）**
  🎉 **合格达标！** 结束生图循环，以第 $i$ 轮为胜出图，进入 Step 3。
- **情况 1b：分数够但未满最小轮次** → 视为未停机，按 `best_direction_hint` 继续叠加（防 1 轮贴原虚高）。
- **情况 2：本轮评分 `< 9.6` 且 $i < 8$**
  🔄 **不合格！** 必须把本轮找出的「不合理之处」转化为具体的叠加修正指令（Overlay Fix），并入第 $i+1$ 轮 Prompt（保留已画对的优点，专门修补本轮缺陷），**立即继续生第 $i+1$ 张图**。
- **情况 3：已满 8 轮（$i = 8$）且评分仍 `< 9.6`**
  🏁 **达到 8 轮上限，停止循环！** 从第 1 ~ 8 轮中**挑选综合评分最高的那一轮图片**作为最终交付图，进入 Step 3。

---

### Step 3：结算最优图 & 自动沉淀记忆（默认静默；全量表需 `--verbose`）

循环结束后，运行：
```bash
python3 pmem_art.py converge finish
```
该命令会自动：
1. 选出达标轮次（`>= 9.6`）或全阶段最高分轮次（`Best of 8`）。
2. 将最终胜出图通过 `ingest` / `feedback` 写入 `.memory-art` 的 `recipe`（正向定稿锚点），并把迭代过程中暴露的典型不合理点写入 `style_redline` / `visual_correction`。
3. 生成标准 Markdown 汇总表。

**对用户的默认展示（静默自动驾驶 · Whisper）：**
1. 🏆 **最终胜出图** + 一句结论（第几轮达标 / 满8轮最高分）。
2. 💡 若 CLI 打出一行 **「小提示」**（如「下次注意：头身比」/「已记住：不要过曝高光」），**原样转述给用户**——整次会话最多 1 条，不要扩写成教练长文。
3. **禁止**向用户旁白「正在写反思 / 更新 taste / 入队 learn / 沉淀红线」；这些已在 `finish`（默认写记忆；`--no-apply` 可跳过） 后台静默完成。
4. 用户没要详情时，**不要**倾倒全轮次评分总表、本轮可学清单、improve/coach/learn 推销。需要全量时让用户加 `--verbose` 或主动说「看报告 / 进步 / 教练」。

### Agent 后台（对用户不可见）
`finish`（默认写记忆；`--no-apply` 可跳过） 已自动：写 recipe/红线 + 会话反思 + `run_silent_autopilot`（更新 taste、强化配方、悄悄 enqueue 1–2 条 learn 建议）。

### 闭环总览（用户几乎无感）
`装上就用 → 画 → 偶尔一行小提示 → 系统自己变强；进阶 peek：improve/coach/learn/progress/--verbose`
## 静默自动驾驶（Agent 必读 · 对用户几乎无感）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-improve` / `/pmem-learn`。
- 对用户只展示：**胜出图 + 结论**；若 stdout 有「小提示」则原样转述（每会话最多 1 条）。
- **不要**叙述「已写入记忆 / 正在自我迭代 / 建议你跑 coach」。用户想看详情时用 `/pmem-improve`·`/pmem-coach`·`python3 pmem_art.py progress`·`--verbose`（进阶/可选）。
