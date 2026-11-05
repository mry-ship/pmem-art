### 🎯 自评收敛生图报告 — 一组乐器5x3整表 Cursor版：垫船图参考锁白卡深底不抄船；overview最多重出；美术收敛≤4轮≥9.5

- **目标模块**：`prop.InstrumentMerge`
- **收敛档位 (`--scale`)**：`medium`（目标阈值 `>= 9.50` · 动态达标停机）
- **收敛模式**：`quality`
- **生图模式**：✍️ 纯文本指令收敛模式
- **Warm-Start 置信度**：`0.9`（私有记忆 `1` 条 · 跨项目共享卡 `1` 张）
- **收敛结论**：⚠️ **共执行 4 轮审图（目标阈值 `9.50` 分），未达标，已挑选全阶段最高分**（胜出：第 4 轮 `9.48 / 10.0` 分）
- **最终采用图片**：`c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\prop\instrumentmerge\overview_5x3_cursor_r4.jpg`（综合评分 **`9.48`** · 共 4 轮未达阈值，采用最高分）

#### 📊 全阶段生图迭代评分与优劣分析总表

| 迭代阶段 | 生成图片 | 综合评分 (满分10) | 合理 / 亮点之处 | 不合理 / 缺陷之处 | 下一轮叠加修正策略 | 结果 |
| :---: | :--- | :---: | :--- | :--- | :--- | :---: |
| 第 1 轮初稿 | `c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\prop\instrumentmerge\overview_5x3_cursor_refpad.jpg` | **8.80**<br><small>composition=9.0,lighting_color=8.8,perspective_anatomy=8.9,texture_detail=8.6,spec_style=8.7,flawlessness=8.8</small> | 5x3白卡深底在;15格乐器无船;物种链可读 | 软塑胶厚实感弱于参考偏2D描边;末档钢琴与前档体量阶差不够一眼;部分格(口琴/竖笛)占卡偏小挤边不齐 | 垫船图重出:加强每格软塑胶圆润体积与统一棚光;L1到L15占卡略递增末档最大;格内居中留边一致;仍只换乐器不抄船 | 🔄 继续迭代 |
| 第 2 轮精修 | `c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\prop\instrumentmerge\overview_5x3_cursor_r2.jpg` | **9.13**<br><small>composition=9.3,lighting_color=9.1,perspective_anatomy=9.2,texture_detail=9.0,spec_style=9.1,flawlessness=9.1</small> | 塑胶质感比R1厚;5x3乐器链仍完整无船 | L15钢琴相对L11低音提琴占卡提升仍偏弱;竖笛/口琴格留边仍略跳;部分高光偏亮接近油光 | 垫船图再出:末三格体量明显最大;全格居中留边对齐;高光收成短软接触光勿油亮 | 🔄 继续迭代 |
| 第 3 轮精修 | `c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\prop\instrumentmerge\overview_5x3_cursor_r3.jpg` | **7.52**<br><small>composition=8.8,lighting_color=8.9,perspective_anatomy=8.7,texture_detail=8.8,spec_style=6.5,flawlessness=6.0</small> | 白卡深底与多数乐器格仍在 | 第3行第4格(L14)是米色游艇不是竖琴;题材串船硬伤 | 垫船图重出:L14必须金三角竖琴;全表禁止任何船/游艇;其余14件乐器保持链序 | 🔄 继续迭代 |
| 第 4 轮精修 | `c:\Users\ZhengLangPC\Desktop\Cursor-Pmem-Art\assets\prop\instrumentmerge\overview_5x3_cursor_r4.jpg` | **9.48**<br><small>composition=9.5,lighting_color=9.4,perspective_anatomy=9.5,texture_detail=9.4,spec_style=9.6,flawlessness=9.5</small> | L14竖琴归位全表无船;5x3白卡深底与乐器链完整 | 竖笛占卡仍略瘦于邻格;体量阶差比image2.5版略弱 | 质感：锐化轮廓与材质分界，抑制融化边缘，勿用噪点冒充细节；竖笛占卡仍略瘦于邻格;体量阶差比image2.5版略弱 | 🔄 继续迭代 |

#### 📚 本轮可学（能力提升）

- **[line_edge]** 本轮短板偏「line_edge」：软塑胶厚实感弱于参考偏2D描边;末档钢琴与前档体量阶差不够一眼;部分格(口琴/竖笛)占卡偏小挤边不齐 → _透明底边缘检查：放大 200% 查毛边与漏抠_
- **[keep]** 保留本轮已做对的：5x3白卡深底在;15格乐器无船;物种链可读 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[lighting]** 本轮短板偏「lighting」：L15钢琴相对L11低音提琴占卡提升仍偏弱;竖笛/口琴格留边仍略跳;部分高光偏亮接近油光 → _同一角色固定机位，分别画顶光 / 侧逆光 / 黄金时刻，对比明暗交界_
- **[keep]** 保留本轮已做对的：塑胶质感比R1厚;5x3乐器链仍完整无船 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[style_lock]** 本轮短板偏「style_lock」：第3行第4格(L14)是米色游艇不是竖琴;题材串船硬伤 → _对照 style-lock 色板 HEX 做 1 张「只换动作不换风」练习_
- **[keep]** 保留本轮已做对的：白卡深底与多数乐器格仍在 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_
- **[line_edge]** 本轮短板偏「line_edge」：竖笛占卡仍略瘦于邻格;体量阶差比image2.5版略弱 → _透明底边缘检查：放大 200% 查毛边与漏抠_
- **[material]** 本轮短板偏「material」：竖笛占卡仍略瘦于邻格;体量阶差比image2.5版略弱 → _同形不同材质：金属 / 布 / 陶瓷各一张，锁死高光形状_
- **[keep]** 保留本轮已做对的：L14竖琴归位全表无船;5x3白卡深底与乐器链完整 → _下一轮 Prompt 显式写入这些亮点作为正向锚点_

> 💡 **阶段总结**：本次共迭代 4 轮，最高分为第 4 轮（`9.48` 分），仍留有轻微不足：「竖笛占卡仍略瘦于邻格;体量阶差比image2.5版略弱」，后续可针对该点微调或局部重绘。

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

- **改动预算**：每轮都垫最初的参考图，只在提示词上补还没过的那一处（提示词改动仍 ≤40%） · 停机线 `>= 9.50`
- **本档指令骨架**：原图画风优先：保画风与机位，柔化光影，只抛光已经有的材质和光，不另起一种光，表面那一句不动，只修没过的那一格
- **本档优选微调**：最优方向：光影·空气·介质；可小幅姿态/局部布局

> 💬 **画师可写一句**（对照上表点名维度）：
> `构图松一点` → **75%（默认95%，-20%）**；`光影锁定降到 40%` → **40%（默认75%，-35%）**；或 `升到 medium`

<small>裁判用六维加权调和平均（无瑕疵由看图的人盲评；画师锁定%压过默认，不是上表锁定%本身）：构图15% · 光影色彩15% · 透视与解剖15% · 质感15% · 规格与风格15% · 无瑕疵25%</small>


#### 🧠 已自动沉淀至 `.memory-art` 的记忆条目
- `.memory-art\entries\prop.InstrumentMerge\CHAT20261103180419974RECIPE.md`
- `.memory-art\entries\prop.InstrumentMerge\CHAT20261103180420101REDLINE.md`
- `.memory-art\_reflections\20261103_180420_instrument-5x3-cursor.json`

> 🔇 记忆沉淀已在后台完成（反思 + taste + learn 队列；不对用户旁白）。进阶 peek：`improve run` · `coach` · `learn suggest` · `progress`；只要一行结论用 `--quiet`。

过程板（点开每张图）：`.memory-art/converge/boards/instrument-5x3-cursor/index.html`

