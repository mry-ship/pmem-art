<div align="center">

# pmem-art

**给画师用的 AI 生图助手**（Cursor / Claude Code / Codex）

对话框输入 `/` 就能画。没点名类型时自己认成哪一支，回显一句就做。生图最多 **4 轮**，不够分就继续修，直到 **≥ 9.60**。  
顺带把你随口说的「别赛博 / 这版留着」记进项目，下次少犯同样的错。

![License](https://img.shields.io/badge/license-see%20LICENSE-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Cursor](https://img.shields.io/badge/Cursor-支持-000000)
![Claude Code](https://img.shields.io/badge/Claude%20Code-支持-D97757)
![Skills](https://img.shields.io/badge/美术技能-8-8B5CF6)
![Threshold](https://img.shields.io/badge/合格线-≥9.60-blue)

[📖 使用手册](USER_MANUAL.md) · [技能流程图](docs/skills/flows.html) · [效果图墙](#效果长什么样) · [合成梯 / 克隆实测](#合成梯与风格克隆旧跑分) · [架构](ARCHITECTURE.md)

</div>

---

## 一分钟接入

```bash
git clone https://github.com/mry-ship/pmem-art.git
cd pmem-art
python3 pmem_art.py init --name "MyArtProject"
python3 pmem_art.py skills --install
```

装好后，在 Cursor / Claude Code / Codex 对话框输入 `/`。技能一共 **8 个**，见下一节的 8 行表。多出来的斜杠名字是旧入口，点了会锁进这 8 个里的某一个。

| 场景 | 命令 |
| :--- | :--- |
| 空项目 | `init` → `skills --install` |
| 已有美术目录（不乱移文件） | `bootstrap --mode legacy --roots Art assets` → `accept --all` → `skills --install` |
| 只刷新技能 | `python3 pmem_art.py skills --install` |

---

## 日常怎么用（Skill）

```text
1. 丢图（可选）   把参考图拖进对话
2. 选档           --scale low | medium | high | recompose
3. 出图           生 1 张 → 打分挑刺 → 不到 9.60 就改（最多 4 轮）
```

合成梯多一步：先用文字把八件关系谈到说通（最多 8 稿，这一段不出图），通过后再按上面的 4 轮出图。同框大图只是体量预览。

### 复制即用

```text
/pmem-draw --scale low [拖入参考图] 只修五指与透视，不改构图
/pmem-draw --scale medium [拖入参考图] 保持构图，补侧逆光与材质
/pmem-concept --scale high [拖入参考图] 锁画风与身份，升级戏剧光影
/pmem-draw --scale recompose --recompose-dir "改为运河石拱桥仰视" [拖入参考图]
```

第三行的 `/pmem-concept` 是旧名字，锁进第 1 行「生图」的原画，不是第 9 个技能。

### 8 个技能

技能文件是 **8 个**，下表正好 **8 行**。没点名类型时，直接说想画什么，模型自己认，回显一句后就做。

<table>
<thead>
<tr><th></th><th>技能</th><th>输入</th><th>做什么</th></tr>
</thead>
<tbody>
<tr><td>1</td><td>生图</td><td><code>/pmem-draw</code><br><small><code>/art-draw</code></small></td><td>总入口。自己认成普通图、原画、克隆、变体或镜头包。生图最多 4 轮，合格线 ≥9.6。有参考但没说新题材时，不进克隆。</td></tr>
<tr><td>2</td><td>界面</td><td><code>/pmem-ui</code><br><small><code>/art-ui</code></small></td><td>一整套 HUD / 菜单 / 九宫格。不用单张插画代替。</td></tr>
<tr><td>3</td><td>图标</td><td><code>/pmem-icon</code><br><small><code>/art-icon</code></small></td><td>三档不混：A 桌面母版、B 线性 SVG、C 道具格。</td></tr>
<tr><td>4</td><td>合成梯</td><td><code>/pmem-merge-ladder</code><br><small><code>/art-ladder</code> · <code>/art-merge</code></small></td><td>先用文字过八件关系（最多 8 稿，说不通就不出图），再一档一张正方形。同框只是体量预览。出图最多 4 轮。</td></tr>
<tr><td>5</td><td>锁风格</td><td><code>/pmem-style-lock</code><br><small><code>/art-style</code></small></td><td>从样张抽色板、光影、禁用词。不进自动生图。</td></tr>
<tr><td>6</td><td>审图</td><td><code>/pmem-critique</code><br><small><code>/art-check</code></small></td><td>只打分挑刺，不生图。</td></tr>
<tr><td>7</td><td>归档</td><td><code>/pmem-atlas</code><br><small><code>/art-map</code></small></td><td>散图归位，刷新 <code>art-atlas.html</code>。</td></tr>
<tr><td>8</td><td>教练</td><td><code>/pmem-coach</code><br><small><code>/art-coach</code></small></td><td>进步、短板、知识合在这一条里看。知识卡要你说收下才写入。</td></tr>
</tbody>
</table>

<p><small><strong>旧斜杠名仍能用。</strong> 它们锁进上面某一行，不是额外的技能。</small></p>

<table>
<thead>
<tr><th><small>你输入</small></th><th><small>锁进</small></th></tr>
</thead>
<tbody>
<tr><td><small><code>/pmem-concept</code> · <code>/art-concept</code></small></td><td><small>第 1 行 · 原画。完整句提示词</small></td></tr>
<tr><td><small><code>/pmem-clone-image</code> · <code>/art-clone</code></small></td><td><small>第 1 行 · 克隆。每轮垫最初那张参考；界面空壳、角色眼睛没过不能停</small></td></tr>
<tr><td><small><code>/pmem-variant</code> · <code>/art-variant</code></small></td><td><small>第 1 行 · 变体。换画风，或同一角色的表情 / 动作差分</small></td></tr>
<tr><td><small><code>/pmem-lens-propose</code> · <code>/art-lens</code></small></td><td><small>第 1 行 · 镜头包。只出方案，点选前不生图。没人要几套机位时，不会自动走进来</small></td></tr>
<tr><td><small><code>/pmem-improve</code> · <code>/art-improve</code></small></td><td><small>第 8 行 · 只看进步</small></td></tr>
<tr><td><small><code>/pmem-learn</code> · <code>/art-learn</code></small></td><td><small>第 8 行 · 只看知识。要你说收下才写入</small></td></tr>
</tbody>
</table>

<a id="四档闸门每档允许变什么--禁止变什么"></a>

### 四档改动幅度（选错了用嘴改就行）

| 档位 | 大致在干什么 | 默认锁住什么 |
| :--- | :--- | :--- |
| **`low`** | 修瑕：手、透视毛刺、小边缘 | 机位、姿态、布局、画风、身份 |
| **`medium`**（默认） | 构图不动，补光影与材质 | 同上；允许加强轮廓光 / 空气感 |
| **`high`** | 可以换机位、姿态、戏剧光影 | 画风基因、身份；别塞原图没有的道具 |
| **`recompose`** | 按你写的方向改构图 | 色板笔触、身份；方向写进 `--recompose-dir` |

停机线统一：**≥ 9.60**（`high` / `recompose` 至少跑 2 轮），并内置 **5 项安全收敛护栏**：
1. **每轮垫最初参考图**：`low` / `medium` / `high` / `recompose` 每一轮都垫最初的 `style_ref`，修正只追加进提示词。风格跳跃不垫旧风格图，也不垫上一轮成图。`pad=previous` 仍是显式链式覆盖。
2. **解剖 `< 7.5` 一票否决（熔断）**：全局停机仍以加权总分 `≥ 9.60` 为准，仅当 `透视与解剖 < 7.5`（严重肢体/结构崩坏）时强制禁停重修；看板同时展示 `总分≥9.6` 与 `总分≥9.6 且 解剖≥8.5` 双指标。
3. **前 3 轮不因掉分停**：生图上限就是第 4 轮。到第 4 轮时，若连续 2 轮比历史最高分低超过 `0.5`，交历史最高分那张。
4. **按题材触发 R1 结构底线**：仅人物/生物自动注入关节/握持/双瞳高光底线；纯空镜仅注入透视灭点与接触阴影；UI/图标跳过人体解剖词。
5. **精简回流与评分容错**：单轮 `【回流修正】` 硬限 `≤ 2` 条；评分 API 偶发失败自动重试，绝不灌入泛化套话污染下一轮 Prompt。

嫌某档太死或太放：同档直接加一句话，例如「medium：允许更大冷暖对比，仍禁止换机位」。细则 → [手册附录 A](USER_MANUAL.md#附录-a四档---scale-细则与示例)。

---

## 效果长什么样

### 自我进化总览

![pmem-art 自我进化报告预览](benchmark-evolution-preview.png)

### V8 · 20 Bot（skills_kit · Absolute-5D）

4 案例 ×（原画 / low / medium / high / recompose / 大改）= **20 终图**。这批是旧上限跑的（当时最多 8 轮、停分 ≥9.60）。现在生图上限是 **最多 4 轮**；表里的「8 轮」只说明那一格实际跑了几轮。  
本批均值 **9.14**（≥9.60 达标 **4/20**）。全页：[docs/showcase/pmem_art_images_v8_20bots_showcase.html](docs/showcase/pmem_art_images_v8_20bots_showcase.html)

Grok 三轮优化 best-of（离线 Absolute-5D 均值 **8.504**）：[docs/showcase/grok_best/pmem_art_images_v8_20bots_grok_best_showcase.html](docs/showcase/grok_best/pmem_art_images_v8_20bots_grok_best_showcase.html) · 永久策略与三轮结论：[docs/grok_v8_3round/FINAL_3ROUND_SYNTHESIS_AND_POLICY.md](docs/grok_v8_3round/FINAL_3ROUND_SYNTHESIS_AND_POLICY.md)

#### 案例 01 · 仙侠不夜城

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c01_ref](docs/showcase/v8_frames/c01_ref.jpg) | ![c01_low](docs/showcase/v8_frames/c01_low.jpg) | ![c01_med](docs/showcase/v8_frames/c01_medium.jpg) | ![c01_high](docs/showcase/v8_frames/c01_high.jpg) | ![c01_rec](docs/showcase/v8_frames/c01_recompose.jpg) | ![c01_bold](docs/showcase/v8_frames/c01_bold.jpg) |
| Baseline | **8.96** · 8 轮<br>`7.96 → 8.96` | **9.38** · 8 轮<br>`8.15 → 9.38` | **8.97** · 8 轮<br>`8.38 → 8.97` | **9.60** · 3 轮<br>`9.06 → 9.60` | **9.18** · 8 轮<br>`6.90 → 9.18` |

#### 案例 02 · 粉彩速写少女

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c02_ref](docs/showcase/v8_frames/c02_ref.jpg) | ![c02_low](docs/showcase/v8_frames/c02_low.jpg) | ![c02_med](docs/showcase/v8_frames/c02_medium.jpg) | ![c02_high](docs/showcase/v8_frames/c02_high.jpg) | ![c02_rec](docs/showcase/v8_frames/c02_recompose.jpg) | ![c02_bold](docs/showcase/v8_frames/c02_bold.jpg) |
| Baseline | **8.72** · 8 轮<br>`7.88 → 8.72` | **8.86** · 8 轮<br>`7.99 → 8.86` | **9.35** · 8 轮<br>`9.22 → 9.35` | **9.68** · 6 轮<br>`8.60 → 9.68` | **9.09** · 8 轮<br>`8.10 → 9.09` |

#### 案例 03 · 窗边日光胸像

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c03_ref](docs/showcase/v8_frames/c03_ref.jpg) | ![c03_low](docs/showcase/v8_frames/c03_low.jpg) | ![c03_med](docs/showcase/v8_frames/c03_medium.jpg) | ![c03_high](docs/showcase/v8_frames/c03_high.jpg) | ![c03_rec](docs/showcase/v8_frames/c03_recompose.jpg) | ![c03_bold](docs/showcase/v8_frames/c03_bold.jpg) |
| Baseline · **8.30** | **8.91** · 8 轮<br>`8.91 → 8.91` | **8.81** · 8 轮<br>`8.61 → 8.81` | **9.35** · 8 轮<br>`8.79 → 9.35` | **9.18** · 8 轮<br>`8.21 → 9.18` | **9.66** · 2 轮<br>`8.88 → 9.66` |

#### 案例 04 · 天井峡谷概念

| 📥 原图 | 🤖 low | 🤖 medium | 🤖 high | 🎮 recompose | 🔥 大改 |
| :---: | :---: | :---: | :---: | :---: | :---: |
| ![c04_ref](docs/showcase/v8_frames/c04_ref.jpg) | ![c04_low](docs/showcase/v8_frames/c04_low.jpg) | ![c04_med](docs/showcase/v8_frames/c04_medium.jpg) | ![c04_high](docs/showcase/v8_frames/c04_high.jpg) | ![c04_rec](docs/showcase/v8_frames/c04_recompose.jpg) | ![c04_bold](docs/showcase/v8_frames/c04_bold.jpg) |
| Baseline · **7.06** | **7.97** · 8 轮<br>`7.40 → 7.97` | **8.45** · 8 轮<br>`7.27 → 8.45` | **9.55** · 8 轮<br>`7.96 → 9.55` | **9.70** · 5 轮<br>`→ 9.70` | **9.40** · 8 轮<br>`→ 9.40` |

> 横看：同一原图在 low → medium → high → recompose → 大改 的差异。竖看：R1 到终稿怎么抬分（Absolute-5D Quant）。

### 合成梯与风格克隆（旧跑分）

全页展陈（V8×20 + Merge/Clone，含分数出处）：[docs/showcase/skills-homepage/index.html](docs/showcase/skills-homepage/index.html)

| 技能 | 在测什么 | 稳定性门槛 | 本批结果 |
| :--- | :--- | :--- | :--- |
| **`pmem-merge-ladder`** | Mode A/B/C 同域 beach-candy 整梯；另有早期 Mode C 三新域连胜 | 八格每一格 Absolute-5D ≥9.6 | **A PASS** min 9.8 · **B/C FAIL**（L6 脸红线）· 早期 G1–G3 MET |
| 风格克隆 | Mode B：锁风格 ~95% + **新主体** · REF\|RESULT。现在用 `/pmem-clone-image` 锁进 draw 的克隆合同 | 连续 3 组 OK（每组 icon+char+UI） | **MET** · G1→G2→G3 |

#### Merge ladder · Mode A / B / C（beach-candy）

同源 beach-candy 八格梯 · EXTRA 片（相对 CONTROL 更优或同级）。分数见 [`modes-abc/SCORES.md`](docs/showcase/skills-homepage/assets/merge/modes-abc/SCORES.md)。

| Mode A · 零参考 | Mode B · 单参考垫 | Mode C · 参考整梯+新域 |
| :---: | :---: | :---: |
| ![Mode A sheet](docs/showcase/skills-homepage/assets/merge/modes-abc/modeA-sheet.jpg) | ![Mode B sheet](docs/showcase/skills-homepage/assets/merge/modes-abc/modeB-sheet.jpg) | ![Mode C sheet](docs/showcase/skills-homepage/assets/merge/modes-abc/modeC-sheet.jpg) |
| **min 9.8 PASS** · beach-candy · 零参考 | **min 8.8 FAIL** · beach-candy · 单参考垫<br>（L6 鸭子黑点脸） | **min 8.5 FAIL** · beach-candy · 参考整梯+新域<br>（同 L6 脸红线） |
| ![Mode A compare](docs/showcase/skills-homepage/assets/merge/modes-abc/modeA-compare.jpg) | ![Mode B compare](docs/showcase/skills-homepage/assets/merge/modes-abc/modeB-compare.jpg) | ![Mode C compare](docs/showcase/skills-homepage/assets/merge/modes-abc/modeC-compare.jpg) |

#### Merge ladder · 早期 Mode C 稳定性连胜（G1 / G2 / G3）

较早一轮：连续 3 个**新域** category-swap 均 8/8 ≥9.6（整梯棋盘）。

| G1 · 烘焙厨具 | G2 · 清洁工具 | G3 · 运动装备 |
| :---: | :---: | :---: |
| ![G1 sheet](docs/showcase/skills-homepage/assets/merge/G1/sheet.jpg) | ![G2 sheet](docs/showcase/skills-homepage/assets/merge/G2/sheet.jpg) | ![G3 sheet](docs/showcase/skills-homepage/assets/merge/G3/sheet.jpg) |
| **8/8 ≥9.6** · min cell **9.6** · r02 | **8/8 ≥9.6** · min cell **9.8** · r02 | **8/8 ≥9.6** · min cell **9.7** · r01 |
| ![G1 vs market](docs/showcase/skills-homepage/assets/merge/G1/compare_to_market.jpg) | ![G2 vs market](docs/showcase/skills-homepage/assets/merge/G2/compare_to_market.jpg) | ![G3 vs market](docs/showcase/skills-homepage/assets/merge/G3/compare_to_market.jpg) |

#### Clone Mode B · 风格克隆新主体

G3 连胜终局（icon / char / UI 均 Absolute-5D ≥9.6）：

| ICON · Scroll 9.6 | CHAR · Blacksmith 9.6 | UI · Jackpot 9.6 |
| :---: | :---: | :---: |
| ![scroll](docs/showcase/skills-homepage/assets/clone/G3-icon-scroll/compare_r01.jpg) | ![blacksmith](docs/showcase/skills-homepage/assets/clone/G3-char-blacksmith/compare_r02.jpg) | ![jackpot](docs/showcase/skills-homepage/assets/clone/G3-ui-jackpot/compare_r02.jpg) |
| cannon booster → 卷轴+蜡封 | king T-pose → 铁匠（空手） | unlock chrome → Jackpot 弹窗 |

同批更早过关（仍计入稳定性循环）：

| ICON · Potion 9.6（G2） | UI · Bonus 9.6（G1） |
| :---: | :---: |
| ![potion](docs/showcase/skills-homepage/assets/clone/G2-icon-potion/compare_r01.jpg) | ![bonus](docs/showcase/skills-homepage/assets/clone/G1-ui-bonus/compare_r02.jpg) |

清晰重出 · same subject（Mode B 垫糊图清出，Absolute-5D ≥9.6）：

| ICON · 球械 9.64 | ICON · 玩具炮 9.62 |
| :---: | :---: |
| ![sphere clear](docs/showcase/skills-homepage/assets/clone/clear-icon-sphere-cannon/sidebyside-sphere.jpg) | ![cannon clear](docs/showcase/skills-homepage/assets/clone/clear-icon-sphere-cannon/sidebyside-cannon.jpg) |
| 糊图垫 → 清晰球械 | 糊图垫 → 清晰玩具炮 |

> 分数均来自真实 `SCORES.md` / `REPORT.md` 跑分，不是展示用编造分。

---

## 记忆是干什么的（简单说）

画师日常不用记命令。Skill 跑完会悄悄把「红线、过稿配方、色板」写进项目里的 `.memory-art/`。

你也可以随口沉淀：

```bash
python3 pmem_art.py feedback "太赛博了，别这样画" -m character.Astra
python3 pmem_art.py feedback "这版留着" -m character.Astra -a path/to/keep.png
```

下次再画同角色 / 同场景，Agent 会先翻这些记录，少重复翻车。细节见 [USER_MANUAL.md](USER_MANUAL.md)。

---

## License

见 [LICENSE](LICENSE)。
