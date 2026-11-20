# `/pmem-layer-split` — 场景切块隔离与叠回

把一张完整场景拆成透明 PNG，叠回去应**基本复原原图**。竖图/横图通用。

**还原合同（玩家口径）**  
1. **出图（isolate）硬锁样子 + 完整性**：视角 / 机位 / 姿势 / 外形特征 / 画风要尽量**一模一样**；部位须**完整**（不贴边裁切）；`_crops` 脚印像素是真值，`keep` 只作短槽位标签  
2. **出图时大小·位置可漂**：隔离引擎略放大/略偏可以接受；**比例不可漂**——禁止压扁/拉长（背景用 aspect 垫边 + 叠回 `cover_uniform`）  
3. **拼回（compose）由 Agent/管线快速对准并交摆好的整图**：以 `truth_boxes` / `_footprints.json` 为槽位真值，用 contain + 锚点 + `autofit_scale_to_ref` 对准脚印；交 `_compose_mid.png` + preview + `stack.html`；**禁止为过闸拧框**  
4. **定块/出图后反向验收**：crop 切肢先扩框；isolate 后查贴边/串戏/换样/缺件，再 compose

**引擎（按优先级）**  
1. **优先** `apikey-image` / `gpt-image-2.5`（`--background transparent --image <crop>`）— 真透明、比例稳  
2. **没有可用的 gpt-image-2.5 通路时** → 用 **Cursor GenerateImage** 按同提示词出层；Cursor **无真透明** → 出**不透明隔离底**（默认纯黑），禁止后抠  
3. 对人回复**禁止**展示、复述或索要任何密钥 / `config.json` / token；缺通路时只说「改用 Cursor 生图」即可  

**本地壳（合同实现）**：`pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> …`（Windows；勿用会弹黑框的 `python`）  
**参考旧壳**：`assets/farm77/_compose_v4.py`、`_emit_html_v4.py`（新任务优先走统一 CLI）。

> 批跑/脚本不是合同真值；本 SKILL 才是。闸门数字与 `scripts/pmem_layer_split/defaults.py` 必须同步。

---

## 执行卡 · 拆图层（Agent 必读）

1. 读原图 → 写 `assets/<job>/split_plan.json`（`id/name/z/crop/keep/remove/file`；玩家点名 N 层则 `modules` 含 bg 总数 = N）。
2. `setup` → 看 `_crops_guide.png` + `_crops/`：贴边切肢先扩框再 setup；框够大优先，禁止为过闸收框。
3. 背景优先 gpt-image-2.5；无通路再用 Cursor **不透明隔离底**（默认纯黑），禁止后抠。
4. `isolate` 并行抽未过线层（双垫图：全主体 crop + `_ctx`）；出图硬锁样子/视角/风格，大小位置可漂。
5. `compose` → `gate` → `qa` → `emit`；脚印不过 → 重抽精灵或扩被点名边，禁止拧框凑比例。
6. 结算贴 `layers.md`（或等价可点表）并 `Read` 叠回整图 + 各层散图；`stack.html` 仅旁路。
7. 细则见下方「一次做对的流程 / 闸门与尺寸」；本地壳 `pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> …`。

---

## 统一 CLI

```text
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> setup [--skip-match] [--no-tighten-from-bg]
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> isolate [--workers 4] [--ids a,b] [--force] [--dry-run]
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> compose
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> gate
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> qa
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> emit
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> retry-dirty
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> pipeline          # 默认：背景也优先 gpt-image-2.5
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> pipeline --bg-local  # 可选：本地挖洞底（易糊，仅调试）
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> bg                 # 显式本地挖洞
pyw -3 -u scripts/run_pmem_layer_split.py --job assets/<job> run-local          # 无远端生图干跑
```

Agent 定稿 `split_plan.json` 后，**优先跑 CLI**，不要每 job 再抄一份 `_setup/_compose`。  
`isolate` 若报「无 gpt-image-2.5 通路」：对本批目标层改用 Cursor GenerateImage（垫对应 `_crops/<id>.png`，提示词同 §3/§4），落盘到 `new/` 后继续 `compose`→`gate`→`qa`→`emit`。

---

## 一次做对的流程

### 1. 定块（split_plan）— 准度优先

写 `split_plan.json`：每块 `id / name / z / crop[l,t,w,h] / keep / remove / file`，可选 `grounded`。

#### 1.0 部位数量（玩家点名优先）

- **没点名数量**：Agent 按场景语义自己划（背景空舞台通常单计一层；道具/角色按槽位拆）
- **点名了「拆成 N 个 / N 层 / N 个部位」**：`modules` 总数（含 bg）必须 = **N**，禁止自动多拆或少拆
- **N 是硬约束，划分质量由 Agent 负责**：在凑满 N 的前提下，自己选**更好的语义切法**——
  - 优先：同槽位绑定、遮挡闭合、装修/变身可独立替换的件
  - 该合的合（同一功能组、同一可替换槽 → 一层，如沙发+茶几+留声机）
  - 该拆的拆（互相遮挡、可单独换装、前景压后景 → 分开）
  - 禁止：为凑 N 把无关碎件胡乱拆碎，或把明显该独立的槽硬并成一团
- 玩家若同时点了清单（「男人、吧台、酒柜…」）→ **以点名清单为准**，数量跟清单；清单外不擅自加层
- 只有数量、没清单时：先在回复里用一行写出拟分的 N 个 `id/name`，再写 `split_plan` 并 `setup` 出 guide（可默认项直接执行，不必为「怎么划」再追问一轮，除非身份/题材会划错）

#### 1.1 估框怎么才准（硬流程 · 框必须够大）

Agent 对归一化坐标**天生不准**（竖图更甚）。合同要求按下面走，禁止「整表凭感觉再微调一轮」：

1. **先包全，再留足垫**：第一稿 = 主体外接矩形 + pad **≥0.08**（矛尖/焰/披风/靴底等柔边按 **0.10–0.12** 写）。轮廓必须全包。**禁止**贴边切肢紧框；禁止单框撑到吞并邻槽  
2. **立刻 `setup` → 看 `_crops_guide.png` + `_crops/<id>.png`**：setup **固定再外扩 `CROP_PAD_PLAN=0.10`**，isolate 裁切再加 `CROP_PAD_ISOLATE_EXTRA=0.08`；写出 `_crops/<id>_ctx.png`。plan 原稿框不会被改写（避免反复 setup 越扩越大）  
3. **完整性预检**：任一 `_crops` 主体贴边切开 → **改 plan 该边再 setup**（≥0.04），禁止残缺 crop 出图  
4. **只改被点名的边**：用户说「2 右边切一点」→ 只把该 id 的 `W` 或右缘 +0.02～0.04，**禁止**同时重写整张表  
5. 改完再画 guide 确认；通过后才 `isolate`  
6. 宁可多一轮「单边微调」，也不要一次「全面优化」把已合格框拧坏  
7. **禁止为过闸拧脚印 / 禁止为降 asp 收框**：`fill`/`asp_err`/`feat_match`/`edge_clip` 不过 → **重抽精灵**或**扩**被点名的边；**禁止**把框裁矮/裁窄凑比例（更切肢 → 换样）

对照：`defaults.CROP_PAD_*`；反例：贴边紧框送进模型、为 asp 收框、整表吞并邻槽；`viking_camp_10` 枪架/盾切肢后另造完整件 → 幽灵热点。

#### 1.2 分块语义

- `z`：背景 → 建筑 → 中景道具/角色 → 前景遮挡物（底叶、前段路石、压住别人的桌沿等常最高）
- **同槽位绑定**：食槽边羊跟食槽；轮胎上羊跟轮胎；琴仙跟树桩；池跟船；**枪架+圆盾若互相咬边且单独框会切肢 → 优先同槽一层**（除非玩家点名必须拆开且两框都能包全）  
- **遮挡闭合**：被挡主体要能补全；挡它的前景必须单独成层且 z 更高  
- **重叠框的 z**：相交时更靠后的 id `z` 更小  
- **`grounded`**：`true` 踩地轻接触影；`false` 飞行无落地影；远景建筑可 skip  
- 背景整幅一层；`keep` 写空舞台，`remove` 列尽角色/道具，**勿把角色烤进背景**  
- **`keep`/`remove` 短标签**：框定后 crop 已锁死对象；`keep` 只写槽位身份（约 5～25 词），`remove` 列邻居；**禁止**长文自由描述压过裁切像素——出图以 `_crops/<id>.png` 为准，求一模一样

#### 1.3 部位完整性合同（viking 反向）

单独部位必须是**可叠回的完整精灵**，不是残片：

| 检查 | 通过 | 失败处理 |
|---|---|---|
| crop 包全外轮廓 | 尖端/焰/挂饰/末梢都在框内且四周有垫 | 扩该边 ≥0.03（可到 0.06）后重 setup |
| 框内少串戏 | 邻居可少许，主体清晰 | `remove` 写清；过脏则收边或合槽 |
| 隔离层不贴边 | 透明留白包住主体 | `edge_clip` 闸失败 → 重抽；仍贴边则先扩 crop |
| 遮挡补全 | 被挡处按 crop 风格补全 | 禁止换成另一件道具 |
| 与 crop 同身份 | 同机位/同件库存 | `feat_match` 低 → 重抽，勿靠拧框 |

**禁止**：残缺 crop → 模型「发明」一件更完整但不同几何的新道具（枪架/盾典型翻车）。

### 2. 校准脚印（框图 = 位置+大小，当场冻结）

跑 `setup`：

1. 导出 `_crops/<id>.png` + `_crops_guide.png`  
2. 模板匹配写 `truth_boxes.json`（分 < 0.55 → `calibrate_fail`）  
3. 若已有空舞台 bg 板：按 **原图−bg 差** 收到主体剪影后仍留 **pad≈0.08**（`CROP_PAD_TIGHTEN`）；再固定外扩写出 isolate 用宽松 `_crops/<id>.png`（`CROP_PAD_ISOLATE_EXTRA=0.08`）。**禁止**迭代贴边狂扩（易铺满整图）  
4. 同时写 `_crops/<id>_ctx.png`（整图高亮本槽）+ `_footprints.json`（`locked: true`）——**叠回贴 footprints；出图双垫 crop+ctx**；**不把扩后框写回 plan.crop**  
5. 框仍明显大于剪影且吞邻槽 → **先收 plan 再 setup**；若只是「留足垫」不算过松  
6. `--no-tighten-from-bg` 可关差分成框（仅调试）  

出图尺寸（仅三档；引擎比例常与原图不一致，见 §3 垫边规则）：

| pixel_aspect | `--size` |
|---|---|
| < 0.85 | `1024x1536` |
| 0.85–1.2 | `1024x1024` |
| > 1.2 | `1536x1024` |

`pixel_aspect = (norm_w/norm_h)*(canvas_W/canvas_H)`。面积 < 0.04 → `--quality medium`，否则 `high`。  
**禁止**为凑引擎画布去压扁场景；比例差用左右/上下垫边（`defaults.aspect_pad_rule`），叠回用等比 `cover_uniform`。

### 3. 背景 — 优先 gpt-image-2.5 出一版（禁止默认糊底 · 禁止压扁）

**默认**：`isolate` / `pipeline` **必须对 `bg` 打一次**（整幅 crop 作参考，空舞台）。优先 gpt-image-2.5 真透明/锐利底；无通路时用 Cursor GenerateImage + 纯黑隔离底。

**比例合同（竖图/超长图必守）**：
1. 引擎只有三档 `--size`，与原图像素比常不一致（如原图 409×1024≈0.40，引擎 1024×1536≈0.67）
2. 出图提示必须注入 `aspect_pad_rule(canvas, size)`：比例不一致时，**主景保持原图纵横比**，左右（或上下）用匹配的天空/地面续写垫边；**禁止**把场景压扁/拉长去填满引擎画布
3. 叠回时背景走 **`cover_uniform`**（等比缩放 + 居中裁切）——**禁止** `resize(W,H)` 非等比拉伸
4. 交件背景观感必须与原图同比例，不能「胖了/扁了」

背景提示要点：

```text
EMPTY STAGE BACKGROUND — LOCK camera and architecture to the crop.
KEEP ONLY (slot tag): <keep>
MUST REMOVE: <remove> — do NOT bake into bg.
{aspect_rule}  ← engine vs canvas pad; NEVER squash
SAME camera / proportions / art style. Sharp opaque scenic fill.
```

**本地挖洞（`bg` / `--bg-local`）仅可选**：大洞 inpaint/高斯易糊、拉丝，**不得作为默认交付背景**。只用于离线 `run-local` 或用户明确只要占位底。

### 4. 隔离出图（并行 + 双垫图 · 只抽未过线层）

#### 4.0 垫图合同（玩家口径 · 框全 + 上下文）

**不要指望「一张整图框好所有部件一次性出齐 N 张透明层」**——生图 API 通常只返回一张图，无法稳定拆成 N 份真 alpha；合成整表再切更糟。  
**默认合同：逐层出**，但每一层必须吃够信息：

| 垫图 | 文件 | 作用 |
|---|---|---|
| 主垫 | `_crops/<id>.png` | **宽松**单槽裁切（包全 + 额外垫），样子/机位真值 |
| 副垫 | `_crops/<id>_ctx.png` | **整图**高亮本槽、外区压暗；锁光影/画风/邻接关系，禁止抄邻居 |
| 总览 | `_crops_guide.png` | 给人审框；Cursor 兜底时可一并参考 |

- gpt-image / apikey-image：`--image crop --image ctx`（双垫）  
- Cursor GenerateImage：同样垫 crop；能多图则加 ctx；提示词用 status 里的 `prompt`  
- **禁止**只垫一张贴边切肢的小 crop  

`_crops/<id>.png`（宽松）+ `_crops/<id>_ctx.png` + 冻结 footprints 是主体**样子与槽位**真值。  
**keep/remove 只做短槽位标签**；样子以主垫 crop 为准，要尽量一模一样。  
只抽主体、禁止整砖复刻邻居；大小略漂交给 compose autofit。按 `grounded` 切换阴影句（`defaults.ISOLATE_PROMPT` + `shadow_rule`）。

```text
STRICT ISOLATE — LOCK LOOK to crop pixels (restore-quality split).
Crop = FOOTPRINT LOCK / pixel ground truth. KEEP only names the slot.
Hard locks:
1) SAME camera / perspective / FOV
2) SAME pose / orientation / silhouette
3) SAME features / materials / colors / part inventory as in the crop
4) SAME art style — extract only, do not restyle
5) WHOLE-SUBJECT COMPLETENESS — full subject + transparent margin; no border clipping
Size may drift → compose autofit. No wild hero-zoom.
Extract ONLY listed subject(s). Occlusion→complete hidden parts; no redesign. No squash.
```

- `isolate` 默认并行（`--workers 4`），**含 bg**；跳过 `status=ok`；优先 gpt-image-2.5；**部件双垫 crop+ctx**；bg 提示自动带 `aspect_pad_rule`；部件提示含完整性第 5 条  
- 无 gpt-image-2.5 通路：Agent 用 Cursor GenerateImage 逐层补齐；**必须**垫 `_crops/<id>.png`，有则再垫 `_crops/<id>_ctx.png`；提示词带**样子硬锁 + 完整性**；黑底隔离，勿对人提密钥；大小交给拼回对准  
- 脏层：`retry-dirty` 或 `isolate --ids … --force`  
- 成功写入 `new/` + `layer_status`

#### 4.1 出图后反向验收（本趟必做，再 compose）

对照 `_crops/<id>.png` 与 `new/<file>` 逐层过一遍（`viking_camp_10` 教训）：

1. **残缺/贴边**：矛尖、焰尖、帐篷侧、披风边是否被画幅切开 → 扩 crop 或重抽  
2. **串戏**：邻居身体/家具是否烤进本层 → 重抽并加强 `remove`  
3. **换样**：完整但已不是 crop 里那件（另造枪架/盾）→ 重抽；框本就切肢则先修框  
4. **缺件**：同槽应在的挂饰/壶/毯是否丢失 → 重抽  
5. 通过后再 `compose`→`gate`→`qa`→`emit`；交 `_compose_mid.png`

### 5. 叠回（摆好位置再交件）

画布 = 原图比例（CLI 默认 2×）。Trim 后贴脚印——**交件必须给出已摆好的整图**，不能只交散层：

- 默认 `contain` + 水平居中；优先用 truth 里冻结的 **`px` 像素框**  
- **踩地**（`grounded=true` / 默认）：**底对齐框底**（锁地面槽位）  
- **墙挂**（`grounded=false`）：**框内居中**（锁墙位）  
- **吊灯/悬吊**：`anchor=top-center`（贴框顶，避免居中把灯拽下来）  
- **大小自校准**：相对原图脚印区做 NCC，在 contain 内自动缩小（`scale_mul≤1`），纠正隔离引擎放大特写  
- 框比主体明显更大 → **先收 crop**，不要靠居中硬凑；**禁止为过 fill 闸把门框撑大**  
- **背景：`cover_uniform`（等比缩放+居中裁）**——禁止非等比 `resize(W,H)`  
- 超宽前景：`width` + 底对齐  
- 禁止道具 `cover`、**禁止任何层非等比拉伸**  
- **交件主件**：`_compose_mid.png`（摆好的叠回整图）+ `_compose_preview.png`（原图|叠回|幽灵）+ `stack.html` + `layers.md`；散层 `new/*.png` 为附图

### 6. 自动闸门

| 检查 | 阈值 | 失败 |
|---|---|---|
| `asp_err` | ≤ 0.18 | dirty |
| `fill` | 0.72–1.08（若有 `scale_mul` 则下限 ×scale_mul²） | dirty |
| alpha 均值 | 0.02–0.92 | dirty |
| `feat_match`（相对 `_crops` 蒙版比对） | ≥ 0.42 | dirty（特征/机位漂了） |
| `edge_clip`（不透明质量压在画幅边框上的比例） | ≤ 0.018 | dirty（部位不完整/贴边裁切） |
| 重试 | ≤ 2 | `needs_human` |

只重抽 `dirty`；`ok` 落盘不动。背景看 `mode=cover_uniform`（日志含 `stretch_err`，仅诊断）。

### 7. 定量幽灵 + HTML

- `qa`：MAE / PSNR / 热力；≥28 warn；≥48 fail  
- `emit`：`stack.html` + `layers.md`（可点单图表）  
- 目视：Ghost 40% 咬合、无串戏、遮挡层齐、接地影符合 `grounded`；**背景与部件均无压扁感**

---

## 新旧变身

同一套 crop / z：先新图再换题材旧图；中途不改分块。

---

## 目录

```text
assets/<job>/
  ref_full.(jpg|png)
  split_plan.json
  truth_boxes.json          # 槽位真值（含 px / anchor）
  _footprints.json          # 冻结脚印合同（locked）
  layer_status.json
  _crops/ + _crops_guide.png
  _crops/<id>_ctx.png       # 整图高亮本槽（isolate 副垫）
  new/  new_trim/
  _compose_preview.png
  _compose_metrics.json     # 含 scale_mul
  _placements.json
  _ghost_qa.json
  _ghost_heatmap.png
  stack.html
  layers.md                 # 可点单图表（交件必贴）
```

---

## 闸门与尺寸

见 `scripts/pmem_layer_split/defaults.py`。改阈值或隔离提示词时 **SKILL 与 defaults 同改**。

---


## 交件可见（拆层结算 · Agent 必读）

**硬规矩**：结算必须贴 **可点单图表**，再对表内每一张 `Read` 贴进对话。禁止只列目录、禁止只甩 `stack.html`。

1. 优先贴 `emit` 写出的 `layers.md`（叠回整图 + 幽灵对比 + 全部 `new/*.png` 的 Markdown 可点链接）。
2. 若无 `layers.md`，手写等价表：列「# / 名称 / 可点图」，链接相对仓库根，形如 `[01-bg.png](assets/<job>/new/01-bg.png)`。
3. 对表内每一张图（含 `_compose_mid.png`、`_compose_preview.png`、各层散图）各 `Read` 一次。
4. `stack.html` 仅作旁路预览，不能代替可点单图表。

## 触发

`/pmem-layer-split 按这张图拆图层并叠回` · `分图叠回要幽灵 HTML` · `装修槽位拆件`
