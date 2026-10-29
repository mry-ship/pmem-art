### 🎯 自评收敛生图报告 — UI 9:16 Royal Garden Home greenhouse

- **目标模块**：`ui.RoyalGardenHome`
- **收敛档位 (`--scale`)**：`medium`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：✍️ 纯文本指令收敛模式
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：pmem-ui concept portrait
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 1 轮 `8.67 / 10.0` 分）
- **最终采用图片**：`docs/showcase/homepage_rerun_1029/v2/ui_royal/portrait/r1.jpg`（综合评分 **`8.67`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `docs/showcase/homepage_rerun_1029/v2/ui_royal/portrait/r1.jpg` | **8.67**<br><small>构图8.8/光影8.9/透视8.7/质感8.6/风格8.8/无瑕疵8.4</small> | greenhouse sofa tea gold can lemon rugs overlay labels all present candy glaze | HUD过大挡住沙发地毯，Home钮过大，Garden/Room过饱和，x3绿圆不是金釉 | 缩小顶栏与Home钮，沙发茶具地毯仍完整可见，Garden 12与Room 3改香槟金釉，x3跟浇水壶同一金釉 | 🔄 继续迭代 |
| 第 2 轮精修 | `docs/showcase/homepage_rerun_1029/v2/ui_royal/portrait/r2.jpg` | **8.36**<br><small>构图8.4/光影8.8/透视8.5/质感8.7/风格8.3/无瑕疵7.8</small> | champagne gold HUD, sofa tea rugs lemon gold can visible | lost greenhouse glass roof; duplicate Garden 12; 120/500 on a flower not watering can; badges left the left stack；prompt 改动 74% 超过档位上限 40% | restore greenhouse glass roof filling the screen; one Garden 12; watering-can 120/500 x3 on the same gold chip; left badges flower teacup sun | 🔄 继续迭代 |
| 第 3 轮精修 | `docs/showcase/homepage_rerun_1029/v2/ui_royal/portrait/r3.jpg` | **8.41**<br><small>构图8.9/光影9.0/透视8.9/质感8.9/风格8.8/无瑕疵7.2</small> | greenhouse sofa tea gold can lemon rugs watering-can bar badges | garbage text LEFT LEFT LEFT on badges; extra five hearts; extra star row | delete LEFT captions, one infinity heart, star 6 only | 🔄 继续迭代 |
| 第 4 轮精修 | `docs/showcase/homepage_rerun_1029/v2/ui_royal/portrait/r4.jpg` | **8.47**<br><small>构图8.3/光影8.8/透视8.8/质感8.8/风格8.4/无瑕疵8.0</small> | infinite heart, 2860, timer, watering-can 120/500 x3, gold bell, greenhouse sofa rugs | badges became leaf flower butterfly not teacup sun; star 6 floats in the room; cream not butter yellow | restore flower teacup sun left badges, park star 6 in the top bar | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[color_palette]** 本轮短板偏「color_palette」：HUD过大挡住沙发地毯，Home钮过大，Garden/Room过饱和，x3绿圆不是金釉 → _从模块 palette 抽 3 HEX 做限色练习，禁止引入霓虹辅色_
- **[keep]** 保留本轮已做对的：greenhouse sofa tea gold can lemon rugs overlay labels all present candy glaze → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：lost greenhouse glass roof; duplicate Garden 12; 120/500 on a flower not waterin → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：champagne gold HUD, sofa tea rugs lemon gold can visible → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：garbage text LEFT LEFT LEFT on badges; extra five hearts; extra star row → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：greenhouse sofa tea gold can lemon rugs watering-can bar badges → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：badges became leaf flower butterfly not teacup sun; star 6 floats in the room; c → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：infinite heart, 2860, timer, watering-can 120/500 x3, gold bell, greenhouse sofa → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 1 轮（`8.67` 分），仍留有轻微不足：「HUD过大挡住沙发地毯，Home钮过大，Garden/Room过饱和，x3绿圆不是金釉」，后续可针对该点微调或局部重绘。

#### 🎚️ 本局档位合同（六维锁定%表 · 画师据此判断大改空间）

**目前是 MEDIUM 档**：中强度 · 小优化（锁机位）。
一览：`构图85%(+0) · 光影色彩30%(+0) · 透视与解剖55%(+0) · 质感35%(+0) · 规格与风格90%(+0) · 无瑕疵90%(+0)`

下表 **六维全部列出**（有效% · 本档默认% · 相对增减 ±%），方便对照往哪调；未改的维显示 **+0%**：

| 维度 | 锁定%（有效 · 默认 · 相对增减） | 含义 |
| :--- | :---: | :--- |
| 构图 | **85%**（默认85%，**+0%**） | 锁机位；允许局部布局微调，禁止整体 recompose |
| 光影色彩 | **30%**（默认30%，**+0%**） | 本档主战场：光影层次、空气感、介质 |
| 透视与解剖 | **55%**（默认55%，**+0%**） | 允许小幅姿态；可修局部结构 |
| 质感 | **35%**（默认35%，**+0%**） | 材质与边缘可抛光 |
| 规格与风格 | **90%**（默认90%，**+0%**） | 画风与身份几乎不动 |
| 无瑕疵 | **90%**（默认90%，**+0%**） | 脏点必须修；这一维由看图的人打，不靠空话 |

- **改动预算**：每轮都垫最初的参考图，只在提示词上补还没过的那一处（提示词改动仍 ≤40%） · 停机线 `>= 9.60`
- **本档指令骨架**：胶片逆光轻厚涂：保画风与机位，整理景深和颗粒，不加成绘画笔触
- **本档优选微调**：最优方向：光影·空气·介质；可小幅姿态/局部布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图15% · 光影色彩22% · 透视与解剖11% · 质感15% · 规格与风格11% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_ui_royal/index.html`

