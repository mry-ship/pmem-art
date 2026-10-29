### 🎯 自评收敛生图报告 — NEAR-BLACK ink hair (charcoal #1A1C22) with only cool window sheen on surface strands. NOT blue dye, NOT teal, NOT navy fashion dye. Light blue eyes, white cat clip, black over-ear headphones, loose opaque white cotton tee, warm gold window light and leaf shadows, white cosmos flowers. Commercial anime paint. 3:4 window portrait. Scale=recompose. Three-quarter BACK view, face still looking at the window. Keep near-black hair, cat clip, headphones, white tee, cosmos. Old front camera is void.

- **目标模块**：`character.SunlitGirl`
- **收敛档位 (`--scale`)**：`recompose`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c03\ref.jpg`)
- **定向改构图指令 (`--recompose-dir`)**：`three-quarter BACK from behind her left shoulder; face still looking at the right window; old front-portrait camera is void`
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：构图与视角：3:4竖幅窗边胸像。镜头略低于眼平、近正面微侧，人物朝右窗外。头占上半，肩胸占下半。人物略偏左，右侧木窗框与白色大波斯菊压前景角。色板：发色素近黑墨色#1A1C22，阴影#2A2C32，冠顶暖金高光#D4B48A，少量冷窗钢灰反光#4A5568（不是染蓝）。瞳浅蓝#7EB4D8。肤暖金#E8C4A0。白T米白#E8E2D6带叶影。主光右上偏后暖金窗光，叶影打在颊、锁骨、白T。笔触：商业二次元半厚涂/赛璐璐，软发丝，清晰五官线，耳机磨砂黑塑料，棉质不透明宽松白T。锁：近黑发、白猫夹、黑包耳耳机、浅蓝眼、白T、窗光叶影、白波斯菊、3:4胸像机位。不要把头发画成染蓝/青发。
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `8.77 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c03\recompose\r4.jpg`（综合评分 **`8.77`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c03\recompose\r1.jpg` | **8.41**<br><small>构图8.4/光影8.8/透视8.3/质感8.3/风格8.6/无瑕疵8.2</small> | 已换到过肩回望；发色近黑；猫夹耳机白T白花都在 | 仍偏过肩侧脸，后脑勺不够；远侧右眼几乎全露，未到四分之三背面 | 再向背面转一档，后脑与左耳罩更满，远侧右眼被颊发挡住一半 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c03\recompose\r2.jpg` | **8.61**<br><small>构图8.9/光影8.8/透视8.5/质感8.5/风格8.7/无瑕疵8.4</small> | 真换成四分之三背面；发色近黑；猫夹耳机白花都在 | 远侧右眼仍全露；后颈与领口接触略空 | 远侧右眼被颊发挡住一半；后颈领口贴实 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c03\recompose\r3.jpg` | **8.57**<br><small>构图8.8/光影8.7/透视8.6/质感8.5/风格8.7/无瑕疵8.3</small> | 背面机位保住；发色近黑 | 远侧右眼仍全露；后背叶影比上一轮弱 | 远侧右眼被颊发挡住一半；后背叶影加回，机位仍是背面 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c03\recompose\r4.jpg` | **8.77**<br><small>构图9.0/光影9.0/透视8.7/质感8.6/风格8.8/无瑕疵8.6</small> | 背面机位加回望；后背叶影加回；发色近黑 | 近乎全侧面，远眼几乎看不见，四分之三背面略过头 | 略转回一点让远眼露出半只 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[style_lock]** 本轮短板偏「style_lock」：仍偏过肩侧脸，后脑勺不够；远侧右眼几乎全露，未到四分之三背面 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：已换到过肩回望；发色近黑；猫夹耳机白T白花都在 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：远侧右眼仍全露；后颈与领口接触略空 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：真换成四分之三背面；发色近黑；猫夹耳机白花都在 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：远侧右眼仍全露；后背叶影比上一轮弱 → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：背面机位保住；发色近黑 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：近乎全侧面，远眼几乎看不见，四分之三背面略过头 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：背面机位加回望；后背叶影加回；发色近黑 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`8.77` 分），仍留有轻微不足：「近乎全侧面，远眼几乎看不见，四分之三背面略过头」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：胶片逆光轻厚涂：按「three-quarter BACK from behind her left shoulder; face still looking at the right window; old front-portrait camera is void」换机位，镜头语言和颗粒不动
- **改构图方向**：`three-quarter BACK from behind her left shoulder; face still looking at the right window; old front-portrait camera is void`
- **本档优选微调**：最优方向：只写目标机位与布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图15% · 光影色彩22% · 透视与解剖11% · 质感15% · 规格与风格11% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c03_recompose/index.html`

