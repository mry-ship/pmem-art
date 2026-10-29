### 🎯 自评收敛生图报告 — Mode A 1024 square one hammer-and-anvil glyph with ember 75 percent safe zone not a forge scene no letters

- **目标模块**：`icon.AppForge`
- **收敛档位 (`--scale`)**：`high`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：✍️ 纯文本指令收敛模式
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：Mode A glyph no screenshot
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 1 轮 `9.07 / 10.0` 分）
- **最终采用图片**：`docs/showcase/homepage_rerun_1029/v2/icon_a3/r1.jpg`（综合评分 **`9.07`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `docs/showcase/homepage_rerun_1029/v2/icon_a3/r1.jpg` | **9.07**<br><small>识别度9.2/安全区9.0/光影质感9.1/多尺寸合规9.0/色板纯粹9.2/无瑕疵9.0</small> | hammer and anvil ember glyph, square, no letters, not a scene | hammer separated from anvil, splits at 29px | rest hammer on anvil as one combined glyph, pull into 75 percent, fewer sparks | 🔄 继续迭代 |
| 第 2 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_a3/r2.jpg` | **8.58**<br><small>识别度8.4/安全区8.8/光影质感8.7/多尺寸合规8.2/色板纯粹9.0/无瑕疵8.5</small> | hammer on anvil, ember contact, no letters | became a 3D product shot; hammer reads slightly as an axe | graphic logo glyph, hammer on anvil as one compact mark, ember edge, micro-bevel, not a product photo | 🔄 继续迭代 |
| 第 3 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_a3/r3.jpg` | **8.87**<br><small>识别度9.0/安全区8.6/光影质感9.0/多尺寸合规8.8/色板纯粹9.2/无瑕疵8.8</small> | hammer on anvil ember indigo field no letters | still a 3D object pair, sparks extra, anvil a bit large | compact into 75 percent, fewer sparks, more logo micro-bevel | 🔄 继续迭代 |
| 第 4 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_a3/r4.jpg` | **7.20**<br><small>识别度8.5/安全区7.2/光影质感9.0/多尺寸合规8.6/色板纯粹9.0/无瑕疵8.0</small> | ember combined mark | pre-rounded squircle with black corners; hammer reads as a pickaxe | full-bleed sharp square, claw hammer on anvil as one glyph | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[style_lock]** 本轮短板偏「style_lock」：hammer separated from anvil, splits at 29px → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：hammer and anvil ember glyph, square, no letters, not a scene → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：became a 3D product shot; hammer reads slightly as an axe → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：hammer on anvil, ember contact, no letters → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：still a 3D object pair, sparks extra, anvil a bit large → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：hammer on anvil ember indigo field no letters → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：pre-rounded squircle with black corners; hammer reads as a pickaxe → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：ember combined mark → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 1 轮（`9.07` 分），仍留有轻微不足：「hammer separated from anvil, splits at 29px」，后续可针对该点微调或局部重绘。

#### 🎚️ 本局档位合同（六维锁定%表 · 画师据此判断大改空间）

**目前是 HIGH 档**：高强度 · 大胆跃升+可叙事。
一览：`构图30%(+0) · 光影色彩20%(+0) · 透视与解剖40%(+0) · 质感35%(+0) · 规格与风格70%(+0) · 无瑕疵80%(+0)`

下表 **六维全部列出**（有效% · 本档默认% · 相对增减 ±%），方便对照往哪调；未改的维显示 **+0%**：

| 维度 | 锁定%（有效 · 默认 · 相对增减） | 含义 |
| :--- | :---: | :--- |
| 构图 | **30%**（默认30%，**+0%**） | 允许机位/布局/元素数为张力与叙事服务 |
| 光影色彩 | **20%**（默认20%，**+0%**） | 只抬这一家已经有的光；体积光只在厚涂 |
| 透视与解剖 | **40%**（默认40%，**+0%**） | 姿态可动，仍保身份可读 |
| 质感 | **35%**（默认35%，**+0%**） | 材质可跟光影一起升级 |
| 规格与风格 | **70%**（默认70%，**+0%**） | 锁媒介基因；no_identity_swap 可加风格内点缀 |
| 无瑕疵 | **80%**（默认80%，**+0%**） | 脏点必须修；这一维由看图的人打，不靠空话 |

- **改动预算**：每轮都垫最初的参考图；第 1 轮可以拉开光影，之后只在提示词上补还没过的那一处（提示词改动仍 ≤80%） · 停机线 `>= 9.60`
- **本档指令骨架**：原图画风优先：保媒介与身份，只抬已经看得见的层次
- **本档优选微调**：最优方向：只抬参考里已经有的层次

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图15% · 光影色彩15% · 透视与解剖15% · 质感15% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_icon_a_forge/index.html`

