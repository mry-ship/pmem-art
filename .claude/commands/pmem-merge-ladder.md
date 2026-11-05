---
description: 同域合成梯：先定链型与关系，再按交付出图（pmem-art）
---

# `/pmem-merge-ladder` — 同域合成梯

## 怎么用（复制即用）
```text
/pmem-merge-ladder 一组建筑；chain_mode=shop_ladder
/pmem-merge-ladder 青瓷药瓶同物件八档：空瓶→塞→半药→满药→签环→金托→晶冠→罩瓶；chain_mode=same_object
/pmem-merge-ladder 节日五条 L1 参考，各 1–6 级同店升级；chain_mode=shop_ladder；levels=6
/pmem-merge-ladder [附船图格子参考] 一组乐器；参考咋排就咋出；垫参考锁白卡深底；不抄船
/pmem-merge-ladder 青瓷药瓶八档；一档一张正方形；chain_mode=same_object
```

一条合同。**merge 本身就是一组**：默认整表一次出齐。有附图时**先认参考是不是整表格子**，再定链型、档数、交付。

## 章节导航

本表只标章节。链型、五问、验收和禁区以原节为准。

| 现在要做 | 读 |
| :--- | :--- |
| 认附图是不是整表格子 | 「开场 0」 |
| 定链型、档数、交付 | 「开场必选」 |
| 写画风一句 | 「风格」 |
| 写关系稿 | 「第一段」 |
| 出整表 | 「出图」的 overview_sheet，「第二段 · 美术」的 overview_sheet |
| 出逐格 | 「出图」的 per_cell，「第二段 · 美术」的 per_cell |
| 看禁区 | 「禁止」 |

## 开场 0 · 整表参考闸（有附图先做；写进第 1 稿）

附图若是多格白圆角卡 / 深灰底图集（常见 3×3=9、4×3=12、5×3=15），视为**整表版式参考**：

1. **先数行列**（目视或脚本），写入 `grid_rows` × `grid_cols` 与 `levels = 格数`。
2. **强制** `delivery=overview_sheet`。禁止默默走 `per_cell` 逐格狂刷。
3. **出图必须垫这张参考**：锁白卡、深灰底、间距、软塑胶质感与棚光；只把格内物件换成玩家题材（乐器/糖果等）。**不抄**参考里的船/无关物件。
4. 玩家说「参考咋出就咋出 / 按我这张 / 一起出 / 不要单张」→ 同上，不问交付。
5. 格数不在机读允许集 `{6,8,9,12,15}` 时先问一句，或取最接近允许值并在讨论稿写明。

**无格子参考时不要回落逐格。** 默认仍是 `overview_sheet` + `levels=8`（常见排法 2×4）；只有玩家明确要「一档一张 / 逐格 / 单张」才走 `per_cell`。

## 开场必选（第 1 稿写死；拿不准就先问一句，不准闷头出图）

### A. `chain_mode`（三选一；也可省略＝轻门，见下）

| 链型 | 何时用 | 硬约束 |
| :--- | :--- | :--- |
| `same_object` | **同模加装**（药瓶加塞/环/托）：底座不变只焊零件 | 必须 `base_body`；留母体词；`parts_add` 累计可读（或明示替换式升级）。禁礼盒/奖杯等换货主语（走 `shop_ladder`） |
| `shop_ladder` | **同族形变 / 同店升级**（Travel Town·Merge Mansion 主流）：每档可为新形态，锁色相与题材家族；允许换包装/容器 | **不写** `base_body`；每档 `evolve_to` + `merge_why`；禁回退与跨店乱跳；64px 相邻档可分 |
| `species_change` | 换物种但仍同任务域（厨具、一组乐器整表） | 不写 `base_body`；每档 `evolve_to` + `merge_why`；整表乐器/船柜优先这条 |
| （省略） | 旧稿 / 未点名链型 | **轻门**：件数、体量、剪影不复读、`parts_add` 具体；不强制 `family`/`merge_why`/`base_body` |

**商业 merge（禁止只懂叠零件）：** 验同链家族基因 + 相邻档可读进化 + 体量缓增 + 合成理由。有糖果/同店升级信号时先想 `shop_ladder`；同模加装才用 `same_object`；**非糖果未点名则轻门，勿默锁 shop_ladder**。禁止装饰换装（例：糖纸档后突然没纸只换彩带，故事断——例句非唯一题材）。多维透镜见 `docs/MERGE_MULTI_LENS.md`（合两下体验 / 64px 可读 / 稀有度曲线 / 链型 / 色材质 / 套件）。

**商业标尺闸（拿不准就先做；建筑/新题材强制）：** 第 1 稿必须写明对标的**顶级同品类 merge 货柜/棋盘链**名称与档序（例：EverMerge 木屋支线 Log→Timber→Frame→Building→House→Rich→Grand→Mansion）。抽：**链型、密度/犒赏曲线、过程类型**；玩家未点名画风且无风格参考时，**同一对标还要抽品类渲染气质**写入 `surface`（软塑胶棚光、饱和友好、缩略可读、上架货柜完成度）。**禁止垫像素抄物件 / 抄构图机位**（气质≠垫竞品截图）。禁止只靠自拟「棚→屋→城堡」叙事过五问；城堡/地标若在对标游戏里是**另一条链或喂养目标**，禁止默默焊成末档。机读 `relation-judge` 过了但没写对标档序，仍不算可出图。

**过程类型（先认再画；详见 `docs/MERGE_MULTI_LENS.md` §8）：** 同族形变货柜 / 同模加装 / 同域换物种 / 原料→半成品→成品 / 生产者升级 / 碎片修复 / 数量捆扎 / 多轨并列。第 1 稿除 `chain_mode` 外写清过程类型。通用铁律：合两下可倒推；未完成→完成；犒赏材质晚出现；一链一合同；**机读过了 ≠ 商业合理**。

**默认怎么选：**

1. 明确同模加零件 / 工具瓶罐加装 → `same_object`
2. 糖果/甜品包装升级、同店货柜、一档比一档高级形态且未说焊零件 → **`shop_ladder`**；禁止默默把软糖锁成 `same_object`
3. 「一组 X / 多种 X」或整表乐器/船参考 → `species_change`（或 `shop_ladder`）。禁止默默焊单母体。「一组」同时确认交付是整表，不是逐格。
4. 单件 L1：工具瓶罐像加装→可 `same_object` 草案；糖果食物包装进化→先 `shop_ladder` 草案。禁止「有 L1 就默认 same_object」
5. 「零件必须累计」**只约束** `same_object`；不覆盖同族形变 / 一组不同 X
6. **非糖果且未点名链型** → 轻门，**禁止**默锁 `shop_ladder` 或强行 `base_body`

### B. `levels`

- **默认起点 8**（L1–L8）。merge 没给数量先按 8 起草，但**对标后以合理为准**：竞品生物/建造段只有 6 档说得通 → 改为 `levels: 6`（常见 2×3），允许集 `6|8|9|12|15`。
- 玩家点名固定数量 → 跟点名（仍须过商业合理；点名 8 却说不通时要写明取舍，不能默默灌假档）。
- 有整表格子参考：`levels` **跟格数**。禁止无视参考硬做成 8。
- **禁止为凑满默认 8**自创金铠/火焰冠/无过渡堆群；玩家拒绝竞品某末段（如群）时，优先缩短档数或改用竞品确有的单件 denser 犒赏，详见 `MERGE_MULTI_LENS` §9。

### C. `delivery`

| 交付 | 含义 |
| :--- | :--- |
| `overview_sheet`（**默认**） | 关系门过后 **整表一组出齐**；**出图一轮交件**（只生 1 张整表→judge→`finish`，标明是否过线）；第 2 次 `generate` 拒跑。禁止从整表抠格冒充逐格成品。无参考时默认 8 档、常见 2×4；竞品段 6 档说得通 → `levels=6` |
| `per_cell`（仅点名） | 一档一张等大正方形；同框整梯只作体量预览，不是成品（MergePerCell） |

**默认 `overview_sheet`（可默认，不必再问）：** 玩家说 merge / 合成梯 / 一组；无交付点名时。  
**才走 `per_cell`：** 玩家明确说「一档一张 / 逐格 / 单张 / per_cell」。  
**仍强制整表：** 整表格子参考；「整表 / 一起出 / 一次出齐 / 不要逐格 / 参考咋出就咋出」；多轨总览。

**耗时合同（出图一轮交件，banner 须写清）：** ①关系段不出图、最多 **2** 稿（第 1 过了就停）；②整表只生 1 张→judge 1 次→finish，并标明是否 ≥9.5/清单过关；③禁止叠轮重出、禁止垫上一张成图；④禁止 overview 套 ordinary「凑满 4 轮」；⑤商业诊断只打字；⑥未点名逐格必须整表（per_cell 仅点名）。

多轨（多张 L1）时：一个 yaml 多个 `tracks`；`overview_sheet` 可一行一轨。

## 风格（第一段写死一句，第二段照用。只取一条）

1. 玩家写下了风格，就用写下的。
2. **整表格子参考**（开场 0）：表面句写「软塑胶圆润厚实体 + 白圆角卡 + 深灰/炭黑底」等眼睛看见的；**出图垫参考文件**锁版式。不抄参考物件。
3. 单件风格参考、非整表：先跑 `pyw -3 -u pmem_art.py ref-read <参考图路径>`，把看见的表面写成一句。`per_cell` 底写成「透明或纯黑隔离」；小高光不要写成油亮。不垫参考文件（除非锁 L1 外观）。不抄参考无关物件。
4. **风格和参考都没有：** 与商业标尺闸**同一对标**写进 `surface`。本技能默认品类是**休闲 merge 货柜**（Merge Mansion / Travel Town / EverMerge 系通感：软塑胶厚实圆润、棚柔光短接触影、饱和友好、棋盘缩略可读、上架道具完成度）——因为交付物本身是 merge 梯，不是把一切题材都收成 merge。若玩家点名非休闲 merge 画风或对标链本身是另一渲染系，跟点名/对标链，**禁止**再强行盖一层无关软塑胶。不是泛卡通插画、不是金幻换装海报。生物链可有轻表情；道具默认无脸，除非该类竞品本来有脸或玩家点名。关系链已对标商业时，**风格不得回落成无关的泛卡通默认**。仍**禁止**把竞品截图当垫图抄物件脸。

**链型/档序（与风格并列的商业优先）：** 玩家口语当提案；第 1 稿必须先钉同品类竞品档序，再决定 levels 与生长/升级/数量混排。细节见 `docs/MERGE_MULTI_LENS.md` §0.1 / §9。禁止无对标硬凑假档。

**底色闸**：
- `per_cell`：允许透明或纯黑隔离；禁止整格变成白/浅灰方卡底、相框 letterbox。
- `overview_sheet` 且参考是白卡深底图集：白圆角卡在深底上是版式，**允许**；禁止改成满幅白底或拆成单张白卡狂刷。

默认 merge 货柜气质下，产品实拍、油光不锈钢、真实木纹微细节要重扣。只有参考或 brief 明确写实才允许写实。

**域内红线（仍通用）**：糖果/甜品轨禁止默认焊进蛋糕、马卡龙、纸杯蛋糕（除非玩家点名蛋糕店链）。

## 第一段 · 升级链与画风（最多 2 稿，过了就停；先不出图）

**最多 2 稿**（CLI discuss 第 3 稿拒写）。**第 1 稿已过五问 + `relation-judge` + 商业对标档序 + 画风已经写成一句 → 立刻进出图**；第 2 稿只改未过行。禁止凑满空写。机读数字过了、合成说不通，仍然不算定稿；画风已经写成一句才能出图。2 稿仍说不通就停，一张图都不出。

第 1 稿就必须写死：对标链名+档序、过程类型、`chain_mode`（或轻门）、`levels`（跟竞品合理，不硬凑 8）、`delivery`、可选行列、N 行升级、`surface` 一句。没过只改未过行；已说通的锁住。

```bash
pyw -3 -u pmem_art.py converge start --session <merge_id> --goal "merge 关系讨论：<题材>" --module <模块> --route-id merge.ladder
pyw -3 -u pmem_art.py converge discuss --session <merge_id> --round <稿次> --prompt "<链型+N行>" --defects "<没过的是哪一行>" --next-fix "<下一稿只改哪几行>"
```
论述必须带 `--session <merge_id>`（或沿用已 start 的活跃会话）；**禁止**无 `--session` 默认写入 `latest`。

### 六条都要过（全链型）

1. 正好 `levels` 件，`level` 为 1..N 连续。同一任务域，不许串成同色杂物。
2. 每一档画面里将只有一件、居中（或整表中每格一件）。无等级字。**道具默认无脸**；**生物链须有可读眼睛/轻表情**（竞品同类有脸时），禁止抠成无眼空头。数量群档仍算「一件货柜件」。
3. 两件相同的这一档合成下一档。下一档仍是一件，且说得出合成理由。换成同色无关物件，没过。
4. 体量只大一圈。低档占格大半，高档留边。末档最大。**overview 白卡安全区**：整只主体（含冠/尾/翅尖）必须落在圆角卡内并留边，禁止超框切边；scale_pct 上限不是许可顶满溢出。
5. 沿档位更复杂或物件类升级。轻门/`same_object` 看 `parts_add`（累计可读）；`shop_ladder`/`species_change` 看 `evolve_to`。只写「更华丽/加光/特效」没过。缩略图看不出的小饰片也算没过。
6. 相邻 `silhouette` 整句不能相同。  
   - `same_object`：必须 `base_body`，每档留母体词；零件累计或明示替换式升级。  
   - `shop_ladder` / `species_change`：不写 `base_body`；禁止物件类回退；禁止无过渡的跨品类硬跳；写清家族色相/题材基因。  
   - 省略链型：`base_body` 可选；写了就粘住。
7. **禁止装饰换装**：不能既不累计零件、又写不出形变 `merge_why`（例句：糖纸→只换彩带断故事）。

### 独立文本判断 · 五问（任一项「否」→ 改稿，不准出图）

1. 同店/同域吗？家族基因（色相/题材）锁住了吗？过程类型（`MERGE_MULTI_LENS` §8）认对了吗？对标档序写了吗？未点名画风时，`surface` 是否已写**同一对标**的品类气质（而非无关泛卡通）？  
2. 有没有回退到更低档物件类？（含「框架封皮」看起来像降级成无关简陋物）  
3. 有没有缺过渡的大跳档？有没有把另链地标/城堡焊进末档？  
4. 缩略图（约 64px）相邻档能分清吗？L1 是否过满、犒赏材质是否过早？  
5. 升级理由具体吗？轻门/`same_object` 看 `parts_add`；`shop_ladder`/`species_change` 看 `merge_why`（不是「更高级/更华丽」）。形变链允许换包装/容器，但必须说得出「两件同级合成后为何变成这一件」，且最好能倒推。

### 机读 yaml

讨论定稿后写成副本（勿改 canonical）。`tracks.<id>`：

- 推荐写：`chain_mode`、`levels`、`surface`；整表参考可写 `grid_rows` / `grid_cols`
- `same_object` 另加 `base_body`
- `rows[]`：`level` `name` `silhouette` `scale_delta` `scale_pct`  
  - 轻门 / `same_object`：`parts_add`（L1=`—`）  
  - `shop_ladder` / `species_change`：`evolve_to`、`merge_why`（L1 的 `merge_why` 可为 `—`）；`parts_add` 可 `—`

`scale_pct` 单调递增（建议 L1 ≥ 0.58，L8 ≤ 0.80；机读下限约 0.55 / 上限约 0.82）。

```bash
pyw -3 -u pmem_art.py merge relation-judge --file <yaml> --all
```

**exit 0 才能出图。** 旧 canonical（无 `chain_mode`、八行、`parts_add`）仍应能过轻门。写成副本时不要改掉这份 canonical 里已有的 track。

**同范围重跑**（`same_object`）：`surface`、`base_body`、零件链从旧稿抄死；出图句每档重复母体 + 只加本档 `parts_add`。

## 出图

### `delivery=overview_sheet`（默认）

关系过了 → **先开会话 + 合理性 + 出图记账 + finish**，不是「过了关系就闷头出一张交账」：

**会话 id 必显式**（禁止 discuss/generate 默写 `latest`）：取 `<merge_id>`，全程同一值。

1. **开会话 + 合理性（整表也要）**：
```bash
pyw -3 -u pmem_art.py converge start --session <merge_id> --goal "merge overview_sheet：<题材+档数+链型>" --module <模块> --route-id merge.ladder
pyw -3 -u pmem_art.py reasonableness review --id <merge_id> --skill merge \
  --draft "<整表草稿提示词>" --revised "<链型/档序/白卡深底/超框禁令/邻档可分写清的修订句>" \
  --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;single_centered_item=ok;chain_mode_declared=ok;upgrade_reason_concrete=ok;family_or_base_lock=ok;sheet_safe_zone=ok"
```
   不过闸不许出第一张整表。
2. **出图（须进 converge 记账；可用 Cursor GenerateImage / 外部生图，但路径要 generate）**：
```bash
# 生图工具出整表 → 落到 <sheet_rN.png>
pyw -3 -u pmem_art.py converge generate --session <merge_id> --round <N> --image <sheet_rN.png> --prompt "<本轮修订句>"
pyw -3 -u pmem_art.py converge judge --session <merge_id> --round <N> --image <sheet_rN.png> \
  --dims "构图9.0/光影9.0/透视9.0/质感9.0/风格9.0/无瑕疵9.0" \
  --defects "<对照固定清单：超框/邻档/眼睛/白卡/关系…具体部位>" \
  --next-fix "<下一张整表只改哪几条清单项>"
```
- 无参考：默认 `levels=8`，常见 `2×4`；白卡深底或纯深底写进表面句并锁住。
- 有整表格子参考：垫该参考，行列与白卡深底跟参考；格内换题材；`levels` 跟格数。
- 有多张 L1：可垫 L1 锁第 1 列 / 各行首格。
- **玩家说不对 / 重做 / 不要旧逻辑**：禁止垫上一版失败整表；按当前关系稿从零出。
3. **整表固定验收清单（出图一轮交件：生1→judge1；第 2 次 generate 会被 CLI 拒绝）**：
   - [ ] 超框：每格主体（含冠/尾/翅尖）落在白卡/格内并留边
   - [ ] 邻档：缩略约 64px 相邻档可分
   - [ ] 眼睛：生物链每格有可读眼睛/轻表情（道具默认无脸）
   - [ ] 白卡/版式：有参考则跟参考白卡深底；无等级字；一格一件
   - [ ] 五问+链表：关系仍说得通，无回退/大跳档
   - **禁止叠轮重出 / 禁止垫上一张成图**：judge 完就 `finish`；要重做就**新开短会话**，不要垫失败整表。
4. **收束**：出图一轮后必须：
```bash
pyw -3 -u pmem_art.py converge finish --session <merge_id>
```
禁止跳过 `start`/`generate`/`judge`/`finish` 只丢一张散图当终稿。`finish` 交这张时**必须写明过线/未过线**并列出未过项，**禁止继续狂刷**。  
停机看本清单，**禁止**把 overview 当成普通图「凑满 4 轮」。  
禁止整表抠格当逐格成品。多模型对比时禁止把 A 模型整表垫进 B 模型参考。

### `delivery=per_cell`（仅玩家点名逐格；默认仍走整表）

关系过了 → 每一档单独出一张正方形 → `merge audit` → 可选 `normalize` 后再跑一次 audit → 第二段出图一轮交件（每档生1→judge1）。  
同框不是交货（同框整梯只作体量预览）。每档首轮仍过 reasonableness review；`--session` 用本档自己的 id，禁止默写 `latest`。不要把参考图文件垫进生图；不垫对方模型成图做「公平对比」。  
**未点名逐格禁止走本段。**

## 第二段 · 美术

### overview_sheet
首张整表前必须过 `reasonableness`（见上）。整表 **只生 1 张→judge 1 次**（`max_rounds=1`）；不走 per_cell。**必须** `converge start` → `generate`/`judge` → `finish`（过程板可见）；finish 标明是否清单过关/≥9.5。

### per_cell（仅点名逐格）
每档出图一轮交件；表面句原样保留。关系散了或 audit 不过，美术分再高也不算过。禁止叠轮。

```bash
pyw -3 -u pmem_art.py merge audit --dir <目录> --phase1 <yaml> --track <域名>
```

`converge generate` / `judge` / `finish` 记账（均带 `--session`）。默认整表用 overview 验收；点名 `per_cell` 才走本段 audit 闭环。

## 禁止

- 没过 `relation-judge` / 五问就出图。
- **overview_sheet 没过 reasonableness 或固定验收清单就当终稿**。
- **未点名逐格却默认走 `per_cell` 单张狂刷**（merge / 一组 / 合成梯默认必须整表）。
- 有整表格子参考或「一起出」却走 `per_cell` 逐格狂刷。
- 有整表参考却不数行列、不垫参考、硬做成默认 8 档。
- 「一组 X」未说同模加零件却默认 `same_object` 焊单母体。
- 用口味「禁止换物种」压过「一组不同 X」/ `species_change`。
- **非糖果且未点名链型**却默认锁 `shop_ladder`；或未选链型却强行锁 `base_body`。（糖果/同店升级按上文默认可 `shop_ladder`，不算违规。）
- 玩家只要六档却硬凑八档无意义补档。
- 空有链型过关却无视 `docs/MERGE_MULTI_LENS.md`：邻档不可分、无犒赏曲线、合两下说不出理由。
- `overview_sheet` / `per_cell` 审完仍叠轮重出（CLI 第 2 次 `generate` 已拒）。
- 关系第 1 稿已过仍空写凑满 2 稿；或 overview 套 ordinary「凑满 4 轮」。
- 整表 judge 完仍垫上一张成图叠轮。
- 商业诊断再连刷整表（只打字）。
- 未点名 Dark/Tinted 却宣称 App Icon 三态已派生齐套。
- 从同框/整表抠图代替逐格交货（当 `delivery=per_cell` 时）。
- 公平对比时垫对方成图。
- `per_cell` 用白/灰卡底交差；或把整表参考拆成单张白卡狂刷。
- 糖果轨默认焊蛋糕/马卡龙/纸杯蛋糕。
