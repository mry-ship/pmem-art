### 🎯 自评收敛生图报告 — 4:3 oil-pastel crayon paper. Black bob, red hoodie, blue shorts, BOTH legs over-knee BLACK socks, near thigh of the closer leg bare above the sock, white sneakers with black stripes. Diagonal blue-grey crayon background, blush air. No ankle socks, no missing sock, no extra limbs. Scale=high. Bolder lighting and finish, keep identity. Same girl, same sitting silhouette, BOTH over-knee black socks, closer thigh bare. Bolder layered oil-pastel on the red hoodie, stronger paper tooth and flywhite, richer diagonal blue-grey hatch, still soft light and short contact shadow. Do not drop a sock, do not add studio volume light.

- **目标模块**：`character.PastelHoodie`
- **收敛档位 (`--scale`)**：`high`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1028\draw_matrix\c02\ref.jpg`)
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 oil-pastel sitting girl. Camera slight 3/4 from her right-back, body faces right, head turns looking up-right. Left-weighted hip on ground, closer knee raised, far leg extended, far sneaker recedes to the right edge (rear/side of shoe). Black bob, red hoodie #E7554D, blue shorts, BOTH legs over-knee BLACK socks, closer thigh BARE above sock cuff, white sneakers with three black stripes. Paper #FBF7F0, diagonal blue-grey hatch #647893, beige hatch upper-right, peach blush, dry crayon tooth, soft flat light, short hip contact shadow. Do not inherit glued near fingers or far shoe as a crayon smear.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `8.99 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\high\r4.jpg`（综合评分 **`8.99`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\high\r1.jpg` | **8.81**<br><small>构图8.8/光影8.8/透视8.4/质感9.1/风格9.2/无瑕疵8.6</small> | 双袜双鞋层次对上参考：抬膝前景鞋+远鞋后缩，近腿大腿裸露，粉彩层更厚。 | 近手手指仍有粘连；帽衫体积光仍偏平，大胆完成度还不够。 | 分开近手五指；加一层更密的红帽衫粉彩叠层和纸齿飞白，双袜双鞋不要动。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\high\r2.jpg` | **8.36**<br><small>构图7.8/光影8.6/透视8.0/质感9.0/风格8.8/无瑕疵8.0</small> | 双过膝黑袜和近腿裸膝还在，粉彩层更密。 | 坐姿被打开成双膝并拢、两只鞋并排朝向镜头，丢掉参考里抬一膝、远鞋后缩的剪影。；prompt 改动 95% 超过档位上限 80% | 恢复一膝抬起、一腿前伸、远鞋后缩的坐姿剪影；五指分开；帽衫粉彩加厚。双过膝黑袜不动。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\high\r3.jpg` | **8.77**<br><small>构图9.0/光影8.7/透视8.6/质感8.8/风格8.9/无瑕疵8.7</small> | 一膝抬起一腿前伸、远鞋后缩的剪影已找回，双过膝黑袜。 | 粉彩被抹得更滑，纸齿飞白不够；手指仍略大。 | 加回干粉彩纸齿和飞白，不要抹成光滑厚涂；五指自然搭膝。剪影和双袜不动。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\high\r4.jpg` | **8.99**<br><small>构图9.1/光影8.9/透视8.7/质感9.2/风格9.3/无瑕疵8.8</small> | 一膝抬起远鞋后缩剪影稳住，干粉彩纸齿回来，双过膝黑袜。 | 手指仍略大，大胆完成度还差一层更密的排线。 | 解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边；手指仍略大，大胆完成度还差一层更密的排线。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[anatomy]** 本轮短板偏「anatomy」：近手手指仍有粘连；帽衫体积光仍偏平，大胆完成度还不够。 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[keep]** 保留本轮已做对的：双袜双鞋层次对上参考：抬膝前景鞋+远鞋后缩，近腿大腿裸露，粉彩层更厚。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：坐姿被打开成双膝并拢、两只鞋并排朝向镜头，丢掉参考里抬一膝、远鞋后缩的剪影。；prompt 改动 95% 超过档位上限 80% → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：双过膝黑袜和近腿裸膝还在，粉彩层更密。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[anatomy]** 本轮短板偏「anatomy」：粉彩被抹得更滑，纸齿飞白不够；手指仍略大。 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[keep]** 保留本轮已做对的：一膝抬起一腿前伸、远鞋后缩的剪影已找回，双过膝黑袜。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[composition]** 本轮短板偏「composition」：手指仍略大，大胆完成度还差一层更密的排线。 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：手指仍略大，大胆完成度还差一层更密的排线。 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[anatomy]** 本轮短板偏「anatomy」：手指仍略大，大胆完成度还差一层更密的排线。 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`8.99` 分），仍留有轻微不足：「手指仍略大，大胆完成度还差一层更密的排线。」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：粉彩速写轻盈风：抬纸纹、飞白、留白和构图张力，光仍是软光、短接触影
- **本档优选微调**：最优方向：只抬这一媒介已经有的长处

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c02_high/index.html`

