### 🎯 自评收敛生图报告 — 4:3 oil-pastel crayon paper. Black bob, red hoodie, blue shorts, BOTH legs over-knee BLACK socks, near thigh of the closer leg bare above the sock, white sneakers with black stripes. Diagonal blue-grey crayon background, blush air. No ankle socks, no missing sock, no extra limbs. Scale=recompose. Same pastel girl, side half-body, still over-knee black socks, red hoodie, crayon paper. New camera: crop head to mid-thigh. Old sitting full-figure camera is void. Both over-knee black socks remain visible. Not a walking full body.

- **目标模块**：`character.PastelHoodie`
- **收敛档位 (`--scale`)**：`recompose`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1028\draw_matrix\c02\ref.jpg`)
- **定向改构图指令 (`--recompose-dir`)**：`Side half-body of the same girl. Old full-figure sitting camera is void. Crop head to mid-thigh, true side or 3/4 side, seated or still standing. NOT a full-body walking shot. Over-knee black socks still visible under the crop.`
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 oil-pastel sitting girl. Camera slight 3/4 from her right-back, body faces right, head turns looking up-right. Left-weighted hip on ground, closer knee raised, far leg extended, far sneaker recedes to the right edge (rear/side of shoe). Black bob, red hoodie #E7554D, blue shorts, BOTH legs over-knee BLACK socks, closer thigh BARE above sock cuff, white sneakers with three black stripes. Paper #FBF7F0, diagonal blue-grey hatch #647893, beige hatch upper-right, peach blush, dry crayon tooth, soft flat light, short hip contact shadow. Do not inherit glued near fingers or far shoe as a crayon smear.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `9.02 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\recompose\r4.jpg`（综合评分 **`9.02`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\recompose\r1.jpg` | **8.65**<br><small>构图8.6/光影8.7/透视8.2/质感9.0/风格9.1/无瑕疵8.4</small> | 已换成侧半身，旧全身坐姿机位作废；红帽衫、黑bob、过膝黑袜还在。 | 半身裁切里只看见一条过膝黑袜，另一腿几乎裁掉；帽子更像围在颈前而不是搭在后背。 | 半身裁到大腿中段，两条过膝黑袜的袜口都要看见；帽兜仍搭在后背。不要走成全身。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\recompose\r2.jpg` | **8.82**<br><small>构图8.8/光影8.8/透视8.5/质感9.1/风格9.2/无瑕疵8.6</small> | 侧半身成立：头到大腿，两条过膝黑袜口都看见，帽兜在后背。 | 小腿还露出太多，接近坐姿四分之三身而不是半身；远腿袜口被抬膝挡住一点。 | 再往上裁到大腿中段，两条过膝黑袜口都完整露在框里；不要露出鞋子，不要全身。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\recompose\r3.jpg` | **8.88**<br><small>构图8.9/光影8.8/透视8.6/质感9.1/风格9.2/无瑕疵8.7</small> | 鞋已裁掉，侧半身更成立，过膝黑袜还在，帽兜在后背。 | 小腿袜筒仍占满下沿，不是大腿中段裁切；第二条袜口几乎看不见。 | 裁到大腿中段，两条过膝黑袜口都完整露在框里；不要小腿和鞋。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\recompose\r4.jpg` | **9.02**<br><small>构图9.2/光影8.9/透视8.8/质感9.1/风格9.3/无瑕疵8.9</small> | 侧半身成立：头到大腿，两条过膝黑袜口都看见，无鞋无全身走姿。 | 袜筒仍偏长，裁切还没完全停在大腿中段。 | 解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边；袜筒仍偏长，裁切还没完全停在大腿中段。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[composition]** 本轮短板偏「composition」：半身裁切里只看见一条过膝黑袜，另一腿几乎裁掉；帽子更像围在颈前而不是搭在后背。 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[keep]** 保留本轮已做对的：已换成侧半身，旧全身坐姿机位作废；红帽衫、黑bob、过膝黑袜还在。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：小腿还露出太多，接近坐姿四分之三身而不是半身；远腿袜口被抬膝挡住一点。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：侧半身成立：头到大腿，两条过膝黑袜口都看见，帽兜在后背。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[composition]** 本轮短板偏「composition」：小腿袜筒仍占满下沿，不是大腿中段裁切；第二条袜口几乎看不见。 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[keep]** 保留本轮已做对的：鞋已裁掉，侧半身更成立，过膝黑袜还在，帽兜在后背。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[composition]** 本轮短板偏「composition」：袜筒仍偏长，裁切还没完全停在大腿中段。 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：袜筒仍偏长，裁切还没完全停在大腿中段。 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[anatomy]** 本轮短板偏「anatomy」：袜筒仍偏长，裁切还没完全停在大腿中段。 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`9.02` 分），仍留有轻微不足：「袜筒仍偏长，裁切还没完全停在大腿中段。」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：粉彩速写轻盈风：按「Side half-body of the same girl. Old full-figure sitting camera is void. Crop head to mid-thigh, true side or 3/4 side, seated or still standing. NOT a full-body walking shot. Over-knee black socks still visible under the crop.」换机位，纸纹和软光不动
- **改构图方向**：`Side half-body of the same girl. Old full-figure sitting camera is void. Crop head to mid-thigh, true side or 3/4 side, seated or still standing. NOT a full-body walking shot. Over-knee black socks still visible under the crop.`
- **本档优选微调**：最优方向：只写目标机位与布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c02_recompose/index.html`

