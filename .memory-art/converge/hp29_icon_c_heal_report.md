### 🎯 自评收敛生图报告 — Mode C red healing potion cork thick silhouette studio vignette no text

- **目标模块**：`icon.PropHeal`
- **收敛档位 (`--scale`)**：`medium`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：✍️ 纯文本指令收敛模式
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：Mode C heal
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 3 轮 `9.14 / 10.0` 分）
- **最终采用图片**：`docs/showcase/homepage_rerun_1029/v2/icon_c_set/heal_r3.jpg`（综合评分 **`9.14`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `docs/showcase/homepage_rerun_1029/v2/icon_c_set/heal_r1.jpg` | **8.91**<br><small>剪影识别9.0/描边色板8.4/棚拍光9.2/透明底8.6/无字9.8/无瑕疵9.0</small> | red corked potion, dark studio, no text, no charms | missing thick item-icon stroke, too product-photo | add thick dark-gold item outline, keep red liquid and cork, dark void no checker | 🔄 继续迭代 |
| 第 2 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_c_set/heal_r2.jpg` | **8.15**<br><small>剪影识别8.0/描边色板7.6/棚拍光9.0/透明底8.4/无字9.8/无瑕疵8.2</small> | red corked potion still readable | gold circular picture frame around the bottle, stroke is a badge not the item；prompt 改动 83% 超过档位上限 40% | delete the frame; thick stroke hugs the bottle silhouette only | 🔄 继续迭代 |
| 第 3 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_c_set/heal_r3.jpg` | **9.14**<br><small>剪影识别9.3/描边色板9.2/棚拍光8.8/透明底8.6/无字9.8/无瑕疵9.2</small> | red corked potion, stroke hugs bottle, no frame, no text | studio rim light a bit flat vs product | thicker dark-gold rim, stronger studio rim light | 🔄 继续迭代 |
| 第 4 轮精修 | `docs/showcase/homepage_rerun_1029/v2/icon_c_set/heal_r4.jpg` | **8.66**<br><small>剪影识别8.8/描边色板8.0/棚拍光9.0/透明底8.6/无字9.8/无瑕疵8.8</small> | red corked potion, no frame, no text | lost faceted cut, gold glow is not a thick silhouette stroke；prompt 改动 55% 超过档位上限 40% | restore faceted glass and a hugging thick stroke | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[icon_consistency]** 本轮短板偏「icon_consistency」：missing thick item-icon stroke, too product-photo → _5 枚图标同 viewBox/stroke 批量生成后做一致性审查表_
- **[keep]** 保留本轮已做对的：red corked potion, dark studio, no text, no charms → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[icon_consistency]** 本轮短板偏「icon_consistency」：gold circular picture frame around the bottle, stroke is a badge not the item；pr → _5 枚图标同 viewBox/stroke 批量生成后做一致性审查表_
- **[keep]** 保留本轮已做对的：red corked potion still readable → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[lighting]** 本轮短板偏「lighting」：studio rim light a bit flat vs product → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[keep]** 保留本轮已做对的：red corked potion, stroke hugs bottle, no frame, no text → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[icon_consistency]** 本轮短板偏「icon_consistency」：lost faceted cut, gold glow is not a thick silhouette stroke；prompt 改动 55% 超过档位上 → _5 枚图标同 viewBox/stroke 批量生成后做一致性审查表_
- **[keep]** 保留本轮已做对的：red corked potion, no frame, no text → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 3 轮（`9.14` 分），仍留有轻微不足：「studio rim light a bit flat vs product」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：原图画风优先：保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光
- **本档优选微调**：最优方向：光影·空气·介质；可小幅姿态/局部布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图15% · 光影色彩15% · 透视与解剖15% · 质感15% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_icon_c_heal/index.html`

