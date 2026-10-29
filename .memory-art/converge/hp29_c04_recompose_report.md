### 🎯 自评收敛生图报告 — 4:3 ink-and-wash courtyard well looking UP. Ochre/honey/amber brick, readable ink lines, broken wooden stairs, warm light. NOT charcoal grayscale, NOT a spiral staircase as the whole well. Scale=recompose. Old worm's-eye camera is void. From the well MOUTH looking DOWN into the same ochre courtyard, broken stairs, ink wash.

- **目标模块**：`scene.CourtWell`
- **收敛档位 (`--scale`)**：`recompose`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\ref.jpg`)
- **定向改构图指令 (`--recompose-dir`)**：`From the circular stone well mouth looking DOWN into the same ochre courtyard. Foreground: thick circular stone rim. Below: ochre/honey walls, broken wooden stairs, ink-and-wash. Warm light still reads. Not grayscale, not a spiral stair filling the shaft.`
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 worm's-eye looking UP the courtyard well. Four walls converge to a far upper corner. Ochre/honey/amber brick #B49257 #E0A86A, ink-beam #392F1F, paper-white #FEF7DF, cool teal shade #5A6B70. Readable dark ink contours + watercolor wash, edge bloom, highlight as reserved paper white. Broken wooden plank stairs fan across the shaft — NOT a complete spiral staircase filling the well. Warm honey light from upper-left, pale stone slabs upper-right, dark iron scrollwork at far landing. Tiny wall figure on right ochre brick. Solid painted corners, not transparent. Do NOT inherit: charcoal grayscale, monochrome, oily impasto, neon, black studio void, plastic smoothness.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 2 轮 `8.69 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\recompose\r2.jpg`（综合评分 **`8.69`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\recompose\r1.jpg` | **8.46**<br><small>构图8.8/光影8.4/透视8.3/质感8.6/风格8.9/无瑕疵8.0</small> | 机位已换成井口俯视，圆形石沿成立；井内仍是赭色水墨不是灰度。 | 井筒深度不够、庭院被压扁；丢失左下冷青与右壁蜜色对比；四角纸白飞出实色；小人仍糊。 | 保持井口俯视。只改：加深井筒纵深让墙面向下收；恢复左下冷青对右壁蜜赭的冷暖。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\recompose\r2.jpg` | **8.69**<br><small>构图9.0/光影8.8/透视8.5/质感8.8/风格9.0/无瑕疵8.3</small> | 井口俯视机位保住；石沿体积更好；左下冷青回来了。 | 井筒仍偏浅、庭院贴在圆洞上；四角纸白飞出实色；小人仍糊。 | 保持井口俯视。只改：四角用石沿或水墨实色填满不要纸白；井筒再加深，墙面向下收。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\recompose\r3.jpg` | **8.63**<br><small>构图8.9/光影8.8/透视8.6/质感8.8/风格9.0/无瑕疵8.1</small> | 井口俯视保住；左下冷青还在；赭色水墨身份在。 | 四角纸白仍在；井筒深度仍不够。 | 保持井口俯视。只改：石沿铺满四边，画面里不要露出白纸三角；井筒再加深。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\recompose\r4.jpg` | **8.61**<br><small>构图8.9/光影8.8/透视8.6/质感8.8/风格9.0/无瑕疵8.0</small> | 井口俯视机位保住；井内赭色水墨与左下冷青还在。 | 四角纸白仍在，石沿没有铺满画幅；井筒深度仍一般。 | 已满4轮。若续跑：石沿铺满四边不要白纸三角。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[style_lock]** 本轮短板偏「style_lock」：井筒深度不够、庭院被压扁；丢失左下冷青与右壁蜜色对比；四角纸白飞出实色；小人仍糊。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：机位已换成井口俯视，圆形石沿成立；井内仍是赭色水墨不是灰度。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：井筒仍偏浅、庭院贴在圆洞上；四角纸白飞出实色；小人仍糊。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：井口俯视机位保住；石沿体积更好；左下冷青回来了。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：四角纸白仍在；井筒深度仍不够。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：井口俯视保住；左下冷青还在；赭色水墨身份在。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：四角纸白仍在，石沿没有铺满画幅；井筒深度仍一般。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：井口俯视机位保住；井内赭色水墨与左下冷青还在。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 2 轮（`8.69` 分），仍留有轻微不足：「井筒仍偏浅、庭院贴在圆洞上；四角纸白飞出实色；小人仍糊。」，后续可针对该点微调或局部重绘。

#### 🎚️ 本局档位合同（六维锁定%表 · 画师据此判断大改空间）

**目前是 Recompose 档**：定向改构图。
一览：`构图15%(+0) · 光影色彩40%(+0) · 透视与解剖35%(+0) · 质感40%(+0) · 规格与风格75%(+0) · 无瑕疵80%(+0)`

下表 **六维全部列出**（有效% · 本档默认% · 相对增减 ±%），方便对照往哪调；未改的维显示 **+0%**：

| 维度 | 锁定%（有效 · 默认 · 相对增减） | 含义 |
| :--- | :---: | :--- |
| 构图 | **15%**（默认15%，**+0%**） | 按 --recompose-dir 重构机位/布局（主战场） |
| 光影色彩 | **40%**（默认40%，**+0%**） | 可随新机位重铺光影 |
| 透视与解剖 | **35%**（默认35%，**+0%**） | 透视随新机位重建 |
| 质感 | **40%**（默认40%，**+0%**） | 材质跟新构图走 |
| 规格与风格 | **75%**（默认75%，**+0%**） | 画风色板与身份仍偏锁 |
| 无瑕疵 | **80%**（默认80%，**+0%**） | 脏点必须修；这一维由看图的人打，不靠空话 |

- **改动预算**：每轮都垫最初的参考图；第 1 轮落到指定机位，之后只在提示词上补还没过的那一处（提示词改动仍 ≤85%） · 停机线 `>= 9.60`
- **本档指令骨架**：原图画风优先：按「From the circular stone well mouth looking DOWN into the same ochre courtyard. Foreground: thick circular stone rim. Below: ochre/honey walls, broken wooden stairs, ink-and-wash. Warm light still reads. Not grayscale, not a spiral stair filling the shaft.」换机位，纸纹和软光不动
- **改构图方向**：`From the circular stone well mouth looking DOWN into the same ochre courtyard. Foreground: thick circular stone rim. Below: ochre/honey walls, broken wooden stairs, ink-and-wash. Warm light still reads. Not grayscale, not a spiral stair filling the shaft.`
- **本档优选微调**：最优方向：只写目标机位与布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c04_recompose/index.html`

