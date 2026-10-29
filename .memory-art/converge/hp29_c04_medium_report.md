### 🎯 自评收敛生图报告 — 4:3 ink-and-wash courtyard well looking UP. Ochre/honey/amber brick, readable ink lines, broken wooden stairs, warm light. NOT charcoal grayscale, NOT a spiral staircase as the whole well. Scale=medium. Small polish, lock camera and identity, keep color wash. One visible polish: cleaner honey wash on the right ochre brick and sharper ink joints on the pale top-right stone.

- **目标模块**：`scene.CourtWell`
- **收敛档位 (`--scale`)**：`medium`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\ref.jpg`)
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 worm's-eye looking UP the courtyard well. Four walls converge to a far upper corner. Ochre/honey/amber brick #B49257 #E0A86A, ink-beam #392F1F, paper-white #FEF7DF, cool teal shade #5A6B70. Readable dark ink contours + watercolor wash, edge bloom, highlight as reserved paper white. Broken wooden plank stairs fan across the shaft — NOT a complete spiral staircase filling the well. Warm honey light from upper-left, pale stone slabs upper-right, dark iron scrollwork at far landing. Tiny wall figure on right ochre brick. Solid painted corners, not transparent. Do NOT inherit: charcoal grayscale, monochrome, oily impasto, neon, black studio void, plastic smoothness.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `8.95 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\medium\r4.jpg`（综合评分 **`8.95`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\medium\r1.jpg` | **8.75**<br><small>构图9.0/光影9.0/透视8.5/质感8.9/风格9.1/无瑕疵8.3</small> | 机位与赭色水墨锁住；右壁蜜色层染略清；不是灰度。 | 远角与右壁小人肢体仍糊；左壁多出悬挂碎板挤井筒；部分木板灭点不齐。 | 锁机位。只改：右壁小人画出可读四肢；去掉左壁多出来的悬挂碎板，让墙面砖缝继续可读。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\medium\r2.jpg` | **8.89**<br><small>构图9.1/光影9.1/透视8.7/质感9.0/风格9.2/无瑕疵8.5</small> | 机位锁住；右壁蜜色层染干净；右壁小人比上轮清楚。 | 远角落点小人仍糊；左壁仍剩悬挂碎板挡砖缝。；prompt 改动 54% 超过档位上限 40% | 锁机位。只改：远角小人肢体可读；再收掉左壁剩余悬挂碎板。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\medium\r3.jpg` | **8.94**<br><small>构图9.2/光影9.1/透视8.8/质感9.0/风格9.2/无瑕疵8.6</small> | 机位与蜜色层染锁住；远角小人比上轮清楚。 | 左壁仍剩悬挂碎板；远角四肢仍软。 | 锁机位。只改：收掉左壁剩余悬挂碎板；远角小人两臂两腿再分开。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\medium\r4.jpg` | **8.95**<br><small>构图9.2/光影9.1/透视8.9/质感9.0/风格9.2/无瑕疵8.6</small> | 机位与蜜色层染锁住；远角小人比第1轮清楚。 | 左壁仍剩少量悬挂碎板；远角四肢仍偏软。 | 已满4轮。若续跑：收掉左壁剩余碎板。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[narrative_camera]** 本轮短板偏「narrative_camera」：远角与右壁小人肢体仍糊；左壁多出悬挂碎板挤井筒；部分木板灭点不齐。 → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：机位与赭色水墨锁住；右壁蜜色层染略清；不是灰度。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：远角落点小人仍糊；左壁仍剩悬挂碎板挡砖缝。；prompt 改动 54% 超过档位上限 40% → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：机位锁住；右壁蜜色层染干净；右壁小人比上轮清楚。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：左壁仍剩悬挂碎板；远角四肢仍软。 → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：机位与蜜色层染锁住；远角小人比上轮清楚。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：左壁仍剩少量悬挂碎板；远角四肢仍偏软。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：机位与蜜色层染锁住；远角小人比第1轮清楚。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`8.95` 分），仍留有轻微不足：「左壁仍剩少量悬挂碎板；远角四肢仍偏软。」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：原图画风优先：保画风与机位，柔化光影和留白，保持干爽笔触
- **本档优选微调**：最优方向：光影·空气·介质；可小幅姿态/局部布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c04_medium/index.html`

