### 🎯 自评收敛生图报告 — 4:3 oil-pastel crayon paper. Black bob, red hoodie, blue shorts, BOTH legs over-knee BLACK socks, near thigh of the closer leg bare above the sock, white sneakers with black stripes. Diagonal blue-grey crayon background, blush air. No ankle socks, no missing sock, no extra limbs. Scale=medium. Small polish, lock camera and socks. Same sitting pose as the reference. Slightly cleaner dry-pastel hatching on the red hoodie and sharper black over-knee sock cuffs on BOTH legs. Far sneaker still recedes; do not open the pose or put both feet side by side facing the camera.

- **目标模块**：`character.PastelHoodie`
- **收敛档位 (`--scale`)**：`medium`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1028\draw_matrix\c02\ref.jpg`)
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 oil-pastel sitting girl. Camera slight 3/4 from her right-back, body faces right, head turns looking up-right. Left-weighted hip on ground, closer knee raised, far leg extended, far sneaker recedes to the right edge (rear/side of shoe). Black bob, red hoodie #E7554D, blue shorts, BOTH legs over-knee BLACK socks, closer thigh BARE above sock cuff, white sneakers with three black stripes. Paper #FBF7F0, diagonal blue-grey hatch #647893, beige hatch upper-right, peach blush, dry crayon tooth, soft flat light, short hip contact shadow. Do not inherit glued near fingers or far shoe as a crayon smear.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `9.10 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\medium\r4.jpg`（综合评分 **`9.10`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\medium\r1.jpg` | **7.30**<br><small>构图8.1/光影8.6/透视7.3/质感9.0/风格9.0/无瑕疵7.5</small> | 机位大体锁住，干粉彩纸纹和双过膝黑袜在。 | 抬膝前景白鞋缺失，只看见伸直腿侧向的一只鞋；双脚没有参考里的前后层次。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 | 锁机位：抬膝脚回到前景白鞋，远鞋后缩到右缘；双过膝黑袜、近腿大腿裸露不动。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\medium\r2.jpg` | **8.93**<br><small>构图9.0/光影8.8/透视8.7/质感9.1/风格9.2/无瑕疵8.8</small> | 机位锁住，双袜双鞋前后层次对上，粉彩帽衫排线更干净。 | 远鞋仍偏侧立偏大；近手手指略糊。 | 远鞋改成后缩小鞋底；近手五指分开。锁机位和双过膝黑袜。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\medium\r3.jpg` | **9.06**<br><small>构图9.2/光影8.9/透视8.9/质感9.2/风格9.3/无瑕疵8.9</small> | 机位和双鞋前后层次最接近参考，远鞋已后缩，双过膝黑袜。 | 近手手指仍略简；远鞋条纹略糊。；prompt 改动 85% 超过档位上限 40% | 近手五指分开但仍自然搭膝；远鞋后缩小底三条杠更清楚。锁机位双袜。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\medium\r4.jpg` | **9.10**<br><small>构图9.2/光影8.9/透视9.0/质感9.2/风格9.3/无瑕疵9.0</small> | 机位、双袜、双鞋前后层次都锁住，手指比上轮自然。 | 远鞋条纹仍略软，未到9.6。；prompt 改动 94% 超过档位上限 40% | 光影：理顺主光方向与明暗交接，只抬画面里已经有的光；远鞋条纹仍略软，未到9.6。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[composition]** 本轮短板偏「composition」：抬膝前景白鞋缺失，只看见伸直腿侧向的一只鞋；双脚没有参考里的前后层次。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：抬膝前景白鞋缺失，只看见伸直腿侧向的一只鞋；双脚没有参考里的前后层次。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[anatomy]** 本轮短板偏「anatomy」：抬膝前景白鞋缺失，只看见伸直腿侧向的一只鞋；双脚没有参考里的前后层次。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[anatomy]** 本轮短板偏「anatomy」：远鞋仍偏侧立偏大；近手手指略糊。 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：远鞋仍偏侧立偏大；近手手指略糊。 → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：机位锁住，双袜双鞋前后层次对上，粉彩帽衫排线更干净。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[anatomy]** 本轮短板偏「anatomy」：近手手指仍略简；远鞋条纹略糊。；prompt 改动 85% 超过档位上限 40% → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：近手手指仍略简；远鞋条纹略糊。；prompt 改动 85% 超过档位上限 40% → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：机位和双鞋前后层次最接近参考，远鞋已后缩，双过膝黑袜。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[lighting]** 本轮短板偏「lighting」：远鞋条纹仍略软，未到9.6。；prompt 改动 94% 超过档位上限 40% → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[keep]** 保留本轮已做对的：机位、双袜、双鞋前后层次都锁住，手指比上轮自然。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`9.10` 分），仍留有轻微不足：「远鞋条纹仍略软，未到9.6。；prompt 改动 94% 超过档位上限 40%」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：粉彩速写轻盈风：保画风与机位，柔化光影和留白，保持干爽笔触
- **本档优选微调**：最优方向：光影·空气·介质；可小幅姿态/局部布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c02_medium/index.html`

