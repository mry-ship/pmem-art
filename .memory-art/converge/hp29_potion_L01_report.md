### 🎯 自评收敛生图报告 — L01 empty short cut-glass bottle, no cork, no liquid. short cut-glass cartoon potion family, gray empty studio, ONLY a contact shadow, no wooden tray, no table, no crate, no face, no rank text. L1 must occupy most of the square (>=58%).

- **目标模块**：`prop.HealPotionMerge`
- **收敛档位 (`--scale`)**：`medium`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：✍️ 纯文本指令收敛模式
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **收敛结论**：✅ **经过 3 轮迭代达标定稿**（generate 与 judge 分步收敛，第 3 轮达到 `9.63 / 10.0` 分 ≥ `9.60` 分档位目标线即刻停机）
- **最终采用图片**：`docs\showcase\homepage_rerun_1029\v2\merge_potion_l16\L01_r3.jpg`（综合评分 **`9.63`** · 经过 3 轮达标定稿）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `docs\showcase\homepage_rerun_1029\v2\merge_potion_l16\L01_r1.jpg` | **8.74**<br><small>剪影识别8.4/描边色板8.8/棚拍光9.3/透明底9.5/无字9.9/无瑕疵8.7</small> | centered cartoon cut-glass potion on gray studio | gradient bg, sparkles, photoreal | fix named defect only | 🔄 继续迭代 |
| 第 2 轮精修 | `docs\showcase\homepage_rerun_1029\v2\merge_potion_l16\L01_r2.jpg` | **8.76**<br><small>剪影识别8.8/描边色板8.6/棚拍光9.2/透明底9.6/无字9.9/无瑕疵8.5</small> | centered cartoon cut-glass potion on gray studio | opaque ceramic not empty glass | fix named defect only | 🔄 继续迭代 |
| 经过 3 轮达标定稿 | `docs\showcase\homepage_rerun_1029\v2\merge_potion_l16\L01_r3.jpg` | **9.63**<br><small>剪影识别9.7/描边色板9.6/棚拍光9.6/透明底9.8/无字9.9/无瑕疵9.6</small> | centered cartoon cut-glass potion on gray studio | tiny outline only | 已达标，无需继续叠加 | 🏆 **达标定稿** |

#### 📚 本轮可学（能力提升）

- **[style_lock]** 本轮短板偏「style_lock」：gradient bg, sparkles, photoreal → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：centered cartoon cut-glass potion on gray studio → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：opaque ceramic not empty glass → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[style_lock]** 本轮短板偏「style_lock」：tiny outline only → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_


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
- **本档指令骨架**：原图画风优先：保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光，表面那一句不动，只修没过的那一格
- **本档优选微调**：最优方向：光影·空气·介质；可小幅姿态/局部布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图15% · 光影色彩15% · 透视与解剖15% · 质感15% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_potion_L01/index.html`

