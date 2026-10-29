### 🎯 自评收敛生图报告 — 4:3 oil-pastel crayon paper. Black bob, red hoodie, blue shorts, BOTH legs over-knee BLACK socks, near thigh of the closer leg bare above the sock, white sneakers with black stripes. Diagonal blue-grey crayon background, blush air. No ankle socks, no missing sock, no extra limbs. Scale=low. Only repair one local flaw. Keep camera, pose, identity. Keep the exact sitting camera: girl in left two-thirds, closer knee raised, far sneaker receding to the right edge. Only repair: readable separate fingers on the near hand resting on the raised knee, and a real far white sneaker with sole and three black stripes instead of a smear. Neighboring pose, socks, hoodie stay locked.

- **目标模块**：`character.PastelHoodie`
- **收敛档位 (`--scale`)**：`low`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1028\draw_matrix\c02\ref.jpg`)
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 oil-pastel sitting girl. Camera slight 3/4 from her right-back, body faces right, head turns looking up-right. Left-weighted hip on ground, closer knee raised, far leg extended, far sneaker recedes to the right edge (rear/side of shoe). Black bob, red hoodie #E7554D, blue shorts, BOTH legs over-knee BLACK socks, closer thigh BARE above sock cuff, white sneakers with three black stripes. Paper #FBF7F0, diagonal blue-grey hatch #647893, beige hatch upper-right, peach blush, dry crayon tooth, soft flat light, short hip contact shadow. Do not inherit glued near fingers or far shoe as a crayon smear.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `9.04 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\low\r4.jpg`（综合评分 **`9.04`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\low\r1.jpg` | **7.40**<br><small>构图8.0/光影8.7/透视7.4/质感9.0/风格9.0/无瑕疵7.6</small> | 干粉彩斜笔、双过膝黑袜、近腿大腿裸露、帽衫红与纸底对上。 | 近处抬膝那只白鞋失踪，只剩伸直腿上的一只鞋；远鞋不再是参考里后缩的鞋底。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 | 把抬膝的那只脚画回前景白鞋三条黑杠，同时保留后缩的远鞋；双腿仍过膝黑袜。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\low\r2.jpg` | **8.89**<br><small>构图9.0/光影8.8/透视8.6/质感9.1/风格9.2/无瑕疵8.7</small> | 双鞋前后层次回来了：抬膝前景白鞋+远鞋后缩，双过膝黑袜，近腿大腿裸露。 | 远鞋偏大、更像侧立而不是参考里的后缩鞋底；近手手指仍略扁。；prompt 改动 36% 超过档位上限 20% | 把远鞋收成后缩的小鞋底三条杠；近手五指分开搭在抬膝上。机位袜子不动。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\low\r3.jpg` | **8.89**<br><small>构图9.1/光影8.8/透视8.7/质感9.1/风格9.2/无瑕疵8.6</small> | 双袜双鞋前后层次仍在，近腿大腿裸露，机位锁住。 | 近手五指张得太开像爪子；远鞋仍偏侧立。；prompt 改动 94% 超过档位上限 20% | 手指自然搭在抬膝上不要张开成爪；远鞋收成后缩小鞋底。姿态袜子不动。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c02\low\r4.jpg` | **9.04**<br><small>构图9.2/光影8.9/透视8.8/质感9.2/风格9.3/无瑕疵8.9</small> | 手指更自然，远鞋改为后缩，双袜双鞋和近腿裸膝锁住。 | 远鞋体量仍略大；近手仍略简。；prompt 改动 97% 超过档位上限 20% | 解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边；远鞋体量仍略大；近手仍略简。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[composition]** 本轮短板偏「composition」：近处抬膝那只白鞋失踪，只剩伸直腿上的一只鞋；远鞋不再是参考里后缩的鞋底。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：近处抬膝那只白鞋失踪，只剩伸直腿上的一只鞋；远鞋不再是参考里后缩的鞋底。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[anatomy]** 本轮短板偏「anatomy」：近处抬膝那只白鞋失踪，只剩伸直腿上的一只鞋；远鞋不再是参考里后缩的鞋底。；解剖/透视：修正关节连接、持械/手足结构与接触阴影，禁止糊边融边 → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[anatomy]** 本轮短板偏「anatomy」：远鞋偏大、更像侧立而不是参考里的后缩鞋底；近手手指仍略扁。；prompt 改动 36% 超过档位上限 20% → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[narrative_camera]** 本轮短板偏「narrative_camera」：远鞋偏大、更像侧立而不是参考里的后缩鞋底；近手手指仍略扁。；prompt 改动 36% 超过档位上限 20% → _同一场景三种景别（远/中/特写）各一张，只改镜头语言_
- **[keep]** 保留本轮已做对的：双鞋前后层次回来了：抬膝前景白鞋+远鞋后缩，双过膝黑袜，近腿大腿裸露。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[anatomy]** 本轮短板偏「anatomy」：近手五指张得太开像爪子；远鞋仍偏侧立。；prompt 改动 94% 超过档位上限 20% → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_
- **[keep]** 保留本轮已做对的：双袜双鞋前后层次仍在，近腿大腿裸露，机位锁住。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[composition]** 本轮短板偏「composition」：远鞋体量仍略大；近手仍略简。；prompt 改动 97% 超过档位上限 20% → _练 3 张同一主体的三分法 / 居中 / 对角线构图对比，只改构图不改色板_
- **[lighting]** 本轮短板偏「lighting」：远鞋体量仍略大；近手仍略简。；prompt 改动 97% 超过档位上限 20% → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[anatomy]** 本轮短板偏「anatomy」：远鞋体量仍略大；近手仍略简。；prompt 改动 97% 超过档位上限 20% → _手部特写 4 连：张开/握拳/持刀/比耶，锁死五指分离_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`9.04` 分），仍留有轻微不足：「远鞋体量仍略大；近手仍略简。；prompt 改动 97% 超过档位上限 20%」，后续可针对该点微调或局部重绘。

#### 🎚️ 本局档位合同（六维锁定%表 · 画师据此判断大改空间）

**目前是 LOW 档**：低强度 · 贴原修瑕。
一览：`构图95%(+0) · 光影色彩75%(+0) · 透视与解剖80%(+0) · 质感25%(+0) · 规格与风格95%(+0) · 无瑕疵90%(+0)`

下表 **六维全部列出**（有效% · 本档默认% · 相对增减 ±%），方便对照往哪调；未改的维显示 **+0%**：

| 维度 | 锁定%（有效 · 默认 · 相对增减） | 含义 |
| :--- | :---: | :--- |
| 构图 | **95%**（默认95%，**+0%**） | 几乎不改机位、景别与布局 |
| 光影色彩 | **75%**（默认75%，**+0%**） | 不大翻主光；局部明暗可微修 |
| 透视与解剖 | **80%**（默认80%，**+0%**） | 可修硬伤，不改姿态动作 |
| 质感 | **25%**（默认25%，**+0%**） | 本档主战场：边缘、材质、小瑕疵 |
| 规格与风格 | **95%**（默认95%，**+0%**） | 画风笔触、色板与身份几乎不动 |
| 无瑕疵 | **90%**（默认90%，**+0%**） | 脏点必须修；这一维由看图的人打，不靠空话 |

- **改动预算**：每轮都垫最初的参考图，只在提示词上补还没过的那一处（提示词改动仍 ≤20%） · 停机线 `>= 9.60`
- **本档指令骨架**：粉彩速写轻盈风：修纸纹脏点和糊掉的干笔触，不加重光
- **本档优选微调**：最优方向：微质感（瓦当/纸齿/发丝），≤40字

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c02_low/index.html`

