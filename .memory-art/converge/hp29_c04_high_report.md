### 🎯 自评收敛生图报告 — 4:3 ink-and-wash courtyard well looking UP. Ochre/honey/amber brick, readable ink lines, broken wooden stairs, warm light. NOT charcoal grayscale, NOT a spiral staircase as the whole well. Scale=high. Bolder atmosphere, keep ochre ink-wash identity. Raise the existing honey shaft of light and ink-line readability; do not turn charcoal or fill the well with a spiral stair.

- **目标模块**：`scene.CourtWell`
- **收敛档位 (`--scale`)**：`high`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\ref.jpg`)
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 worm's-eye looking UP the courtyard well. Four walls converge to a far upper corner. Ochre/honey/amber brick #B49257 #E0A86A, ink-beam #392F1F, paper-white #FEF7DF, cool teal shade #5A6B70. Readable dark ink contours + watercolor wash, edge bloom, highlight as reserved paper white. Broken wooden plank stairs fan across the shaft — NOT a complete spiral staircase filling the well. Warm honey light from upper-left, pale stone slabs upper-right, dark iron scrollwork at far landing. Tiny wall figure on right ochre brick. Solid painted corners, not transparent. Do NOT inherit: charcoal grayscale, monochrome, oily impasto, neon, black studio void, plastic smoothness.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `8.88 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\high\r4.jpg`（综合评分 **`8.88`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\high\r1.jpg` | **8.40**<br><small>构图9.0/光影9.2/透视8.4/质感8.9/风格9.1/无瑕疵8.1</small> | 蜜金光柱与左下冷青对比拉开，高档氛围成立；赭色水墨身份仍在。 | 远角小人融化；左上多出悬挂杂物挡住砖墙；过曝把左上砖缝冲掉。；透视：收束灭点与体块接触阴影，禁止结构融化 | 保住蜜金光柱。只改：远角小人肢体可读；收掉左上多余悬挂杂物，让砖缝在暖光里仍能读。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\high\r2.jpg` | **8.50**<br><small>构图9.1/光影9.3/透视8.5/质感8.9/风格9.2/无瑕疵8.3</small> | 蜜金光柱与左下冷青仍在；赭色水墨身份未改成炭笔。 | 远角小人仍融化；左上悬挂杂物还在，暖光把砖缝冲淡。；透视：收束灭点与体块接触阴影，禁止结构融化 | 保住蜜金光柱。只改：远角小人肢体可读；收掉左上悬挂杂物并让暖光里的砖缝仍能读。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\high\r3.jpg` | **8.84**<br><small>构图9.1/光影9.2/透视8.6/质感8.9/风格9.2/无瑕疵8.4</small> | 蜜金光柱与冷青对比仍在；赭色水墨未改成炭笔。 | 左上暖光过曝冲掉砖缝；远角小人仍偏糊；左上悬挂杂物还在。 | 保住光柱但收回左上过曝，让砖缝可读；远角小人头肩腿分开。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\high\r4.jpg` | **8.88**<br><small>构图9.1/光影9.3/透视8.6/质感8.9/风格9.2/无瑕疵8.5</small> | 蜜金光柱与冷青对比仍在；赭色水墨身份未改成炭笔。 | 左上仍有悬挂杂物；远角小人仍偏糊。 | 已满4轮。若续跑：收掉左上悬挂并让远角小人肢体分开。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[composition]** 本轮短板偏「composition」：远角小人融化；左上多出悬挂杂物挡住砖墙；过曝把左上砖缝冲掉。；透视：收束灭点与体块接触阴影，禁止结构融化 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：远角小人融化；左上多出悬挂杂物挡住砖墙；过曝把左上砖缝冲掉。；透视：收束灭点与体块接触阴影，禁止结构融化 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[keep]** 保留本轮已做对的：蜜金光柱与左下冷青对比拉开，高档氛围成立；赭色水墨身份仍在。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[composition]** 本轮短板偏「composition」：远角小人仍融化；左上悬挂杂物还在，暖光把砖缝冲淡。；透视：收束灭点与体块接触阴影，禁止结构融化 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：远角小人仍融化；左上悬挂杂物还在，暖光把砖缝冲淡。；透视：收束灭点与体块接触阴影，禁止结构融化 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[keep]** 保留本轮已做对的：蜜金光柱与左下冷青仍在；赭色水墨身份未改成炭笔。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：左上暖光过曝冲掉砖缝；远角小人仍偏糊；左上悬挂杂物还在。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：蜜金光柱与冷青对比仍在；赭色水墨未改成炭笔。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：左上仍有悬挂杂物；远角小人仍偏糊。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：蜜金光柱与冷青对比仍在；赭色水墨身份未改成炭笔。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`8.88` 分），仍留有轻微不足：「左上仍有悬挂杂物；远角小人仍偏糊。」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：原图画风优先：抬纸纹、飞白、留白和构图张力，光仍是软光、短接触影
- **本档优选微调**：最优方向：只抬这一媒介已经有的长处

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c04_high/index.html`

