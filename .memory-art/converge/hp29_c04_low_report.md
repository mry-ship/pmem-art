### 🎯 自评收敛生图报告 — 4:3 ink-and-wash courtyard well looking UP. Ochre/honey/amber brick, readable ink lines, broken wooden stairs, warm light. NOT charcoal grayscale, NOT a spiral staircase as the whole well. Scale=low. Only repair one local flaw: keep wooden structure as BROKEN radiating plank stairs (not a complete spiral filling the shaft) and make the small wall-figure limbs readable. Lock ochre wash and the well camera.

- **目标模块**：`scene.CourtWell`
- **收敛档位 (`--scale`)**：`low`（目标阈值 `>= 9.60` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：🖼️ 垫图解构收敛模式 (`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\ref.jpg`)
- **Warm-Start 置信度**：`0.3`（私有记忆 `0` 条 · 跨项目共享卡 `2` 张）
- **参考图解构基准**：4:3 worm's-eye looking UP the courtyard well. Four walls converge to a far upper corner. Ochre/honey/amber brick #B49257 #E0A86A, ink-beam #392F1F, paper-white #FEF7DF, cool teal shade #5A6B70. Readable dark ink contours + watercolor wash, edge bloom, highlight as reserved paper white. Broken wooden plank stairs fan across the shaft — NOT a complete spiral staircase filling the well. Warm honey light from upper-left, pale stone slabs upper-right, dark iron scrollwork at far landing. Tiny wall figure on right ochre brick. Solid painted corners, not transparent. Do NOT inherit: charcoal grayscale, monochrome, oily impasto, neon, black studio void, plastic smoothness.
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.60` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `8.98 / 10.0` 分）
- **最终采用图片**：`C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\low\r4.jpg`（综合评分 **`8.98`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\low\r1.jpg` | **8.69**<br><small>构图9.1/光影8.9/透视8.5/质感8.8/风格9.0/无瑕疵8.2</small> | 井底仰视机位锁住；赭蜜砖色与墨线成立，不是炭笔灰；碎木梯仍是扇状散板。 | 远角落点小人肢体不可读，仍是一团；右壁小人仍是绿lump+黑团；部分木板不跟同一灭点。 | 只改两处：远角落点小人画出可读头胸四肢；扇状碎木板全部指向同一远上角灭点，保持断裂不要修成完整楼梯。 | 🔄 继续迭代 |
| 第 2 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\low\r2.jpg` | **8.80**<br><small>构图9.1/光影9.0/透视8.6/质感8.9/风格9.1/无瑕疵8.4</small> | 仰视机位与赭蜜水墨仍锁住；右壁小人略可辨；不是灰度。 | 远角落点小人仍偏糊；扇状木板被修得太像完整梯级；左壁仍有多余悬挂碎板。；prompt 改动 64% 超过档位上限 20% | 只改：远角小人画出帽/头、肩、两腿；木板保持断裂空隙，不要连成完整楼梯。 | 🔄 继续迭代 |
| 第 3 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\low\r3.jpg` | **8.94**<br><small>构图9.2/光影9.1/透视8.8/质感9.0/风格9.2/无瑕疵8.6</small> | 远角小人开始能看出帽与身形；仰视机位与赭色水墨锁住。 | 扇状木板仍偏完整梯级；左壁仍有多余碎板；远角四肢还不够分开。；prompt 改动 59% 超过档位上限 20% | 只改：木板之间留出断裂空隙，不要连成完整楼梯；远角小人两臂两腿再分开一点。 | 🔄 继续迭代 |
| 第 4 轮精修 | `C:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\docs\showcase\homepage_rerun_1029\draw_matrix\c04\low\r4.jpg` | **8.98**<br><small>构图9.2/光影9.1/透视8.9/质感9.0/风格9.2/无瑕疵8.7</small> | 远角小人帽与腿比前轮清楚；仰视机位与赭色水墨锁住，不是灰度。 | 扇状木板仍偏完整梯级；左壁仍有少量悬挂碎板。；prompt 改动 61% 超过档位上限 20% | 已满4轮。若续跑：木板再留断裂空隙。 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[style_lock]** 本轮短板偏「style_lock」：远角落点小人肢体不可读，仍是一团；右壁小人仍是绿lump+黑团；部分木板不跟同一灭点。 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：井底仰视机位锁住；赭蜜砖色与墨线成立，不是炭笔灰；碎木梯仍是扇状散板。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：远角落点小人仍偏糊；扇状木板被修得太像完整梯级；左壁仍有多余悬挂碎板。；prompt 改动 64% 超过档位上限 20% → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：仰视机位与赭蜜水墨仍锁住；右壁小人略可辨；不是灰度。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：扇状木板仍偏完整梯级；左壁仍有多余碎板；远角四肢还不够分开。；prompt 改动 59% 超过档位上限 20% → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：远角小人开始能看出帽与身形；仰视机位与赭色水墨锁住。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：扇状木板仍偏完整梯级；左壁仍有少量悬挂碎板。；prompt 改动 61% 超过档位上限 20% → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：远角小人帽与腿比前轮清楚；仰视机位与赭色水墨锁住，不是灰度。 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`8.98` 分），仍留有轻微不足：「扇状木板仍偏完整梯级；左壁仍有少量悬挂碎板。；prompt 改动 61% 超过档位上限 20%」，后续可针对该点微调或局部重绘。

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
- **本档指令骨架**：原图画风优先：修纸纹脏点和糊掉的干笔触，不加重光
- **本档优选微调**：最优方向：微质感（瓦当/纸齿/发丝），≤40字

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图11% · 光影色彩11% · 透视与解剖15% · 质感22% · 规格与风格15% · 无瑕疵25%</small>


过程板（点开每张图）：`.memory-art/converge/boards/hp29_c04_low/index.html`

