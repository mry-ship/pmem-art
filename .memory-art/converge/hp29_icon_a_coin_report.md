### 🎯 自评收敛生图报告 — Mode A 1024 square one celadon-glaze gold coin wet highlight stripe 75 percent safe zone no letters

- **目标模块**：`icon.AppCoin`
- **收敛档位 (`--scale`)**：`high`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：✍️ 纯文本指令收敛模式
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：Mode A glyph no screenshot
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 3 轮 `9.17 / 10.0` 分）
- **最终采用图片**：`docs/showcase/homepage_rerun_1029/v2/icon_a2/r3.jpg`（综合评分 **`9.17`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `docs/showcase/homepage_rerun_1029/v2/icon_a2/r1.jpg` | **8.63**<br><small>识别度8.2/安全区9.2/光影质感8.7/多尺寸合规8.5/色板纯粹9.1/无瑕疵8.4</small> | celadon disc gold rim wet highlight no letters square field | reads as blank badge not a coin, no reeded edge or thickness | add coin reeding and thickness, keep celadon wet stripe, no letters | 🔄 继续迭代 |
| 第 2 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_a2/r2.jpg` | **8.95**<br><small>识别度8.8/安全区9.0/光影质感9.0/多尺寸合规9.1/色板纯粹9.3/无瑕疵8.8</small> | reeded gold edge, celadon face, no letters | reads a bit like a bottle cap; wet highlight blown white | thinner coin facing camera, clean wet stripe, still celadon glaze no letters | 🔄 继续迭代 |
| 第 3 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_a2/r3.jpg` | **9.17**<br><small>识别度8.8/安全区9.3/光影质感9.2/多尺寸合规9.3/色板纯粹9.4/无瑕疵9.2</small> | face-on celadon coin reeded edge clean wet stripe no letters | coin a bit small and slightly cabochon-like | enlarge toward 75 percent, a little more gold thickness, keep stripe | 🔄 继续迭代 |
| 第 4 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_a2/r4.jpg` | **6.80**<br><small>识别度8.0/安全区6.8/光影质感8.5/多尺寸合规7.5/色板纯粹8.5/无瑕疵8.0</small> | reeded celadon coin close-up | fills the frame, not 75 percent safe zone, crackle glaze photo not an app icon | pull back, 75 percent safe zone, even celadon, no crackle photo | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[style_lock]** 本轮短板偏「style_lock」：reads as blank badge not a coin, no reeded edge or thickness → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：celadon disc gold rim wet highlight no letters square field → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：reads a bit like a bottle cap; wet highlight blown white → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：reeded gold edge, celadon face, no letters → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：coin a bit small and slightly cabochon-like → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：face-on celadon coin reeded edge clean wet stripe no letters → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：fills the frame, not 75 percent safe zone, crackle glaze photo not an app icon → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：reeded celadon coin close-up → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 3 轮（`9.17` 分），仍留有轻微不足：「coin a bit small and slightly cabochon-like」，后续可针对该点微调或局部重绘。

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


过程板（点开每张图）：`.memory-art/converge/boards/hp29_icon_a_coin/index.html`

