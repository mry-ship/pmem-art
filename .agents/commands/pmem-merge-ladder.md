---
description: 同域合成梯：先定链型与关系，再按交付出图（pmem-art）
---

# `/pmem-merge-ladder` — 同域合成梯

## 怎么用（复制即用）
```text
/pmem-merge-ladder 青瓷药瓶同物件八档：空瓶→塞→半药→满药→签环→金托→晶冠→罩瓶；chain_mode=same_object；一档一张正方形
/pmem-merge-ladder 节日五条 L1 参考，各 1–6 级同店升级；chain_mode=shop_ladder；delivery=overview_sheet；先文字定链再单次整表
/pmem-merge-ladder [附船图格子参考] 一组乐器；参考咋排就咋出；垫参考锁白卡深底；不抄船
```

一条合同。有附图时**先认参考是不是整表格子**，再定链型、档数、交付。

## 开场 0 · 整表参考闸（有附图先做；写进第 1 稿）

附图若是多格白圆角卡 / 深灰底图集（常见 3×3=9、4×3=12、5×3=15），视为**整表版式参考**：

1. **先数行列**（目视或脚本），写入 `grid_rows` × `grid_cols` 与 `levels = 格数`。
2. **强制** `delivery=overview_sheet`。禁止默默走 `per_cell` 逐格狂刷。
3. **出图必须垫这张参考**：锁白卡、深灰底、间距、软塑胶质感与棚光；只把格内物件换成玩家题材（乐器/糖果等）。**不抄**参考里的船/无关物件。
4. 玩家说「参考咋出就咋出 / 按我这张 / 一起出 / 不要单张」→ 同上，不问交付。
5. 格数不在机读允许集 `{6,8,9,12,15}` 时先问一句，或取最接近允许值并在讨论稿写明。

无整表信号时，才回落到下方默认 `per_cell`（MergePerCell）。

## 开场必选（第 1 稿写死；拿不准就先问一句，不准闷头出图）

### A. `chain_mode`（三选一；也可省略＝轻门，见下）

| 链型 | 何时用 | 硬约束 |
| :--- | :--- | :--- |
| `same_object` | 同一物件加零件（药瓶、软糖） | 必须 `base_body`；每档 `silhouette`/`name` 留母体词；`parts_add` 为具体零件 |
| `shop_ladder` | 同店同品类换货升级（章→杯、袋→箱）；玩家明确说「不必每档带 L1 原件 / 合理换物件升级」 | **不写** `base_body`；每档 `evolve_to` + `merge_why`；禁止回退；禁止跨店乱跳 |
| `species_change` | 换物种但仍同任务域（厨具→厨具、一组乐器） | 不写 `base_body`；每档 `evolve_to` + `merge_why`；同任务域 |
| （省略） | 旧稿 / 未点名链型 | **轻门**（MergePerCell）：只审件数、体量、剪影不复读、`parts_add` 具体；**不**强制 `family`/`merge_why`/`base_body` |

**默认怎么选（通用，勿被单次节日任务带偏）：**

1. 玩家明确同模加零件 → `same_object`
2. 玩家明确换货/同店升级/不必保留 L1 体 → `shop_ladder`
3. 玩家明确换物种同域，或说「一组 X / 多种 X」（乐器、船、厨具）且未说同模加零件 → `species_change`（或 `shop_ladder`）。**禁止**默默锁成一把吉他/一个母体焊零件
4. 只给了**单件** L1 参考、没说换不换物件 → **先按 `same_object` 草案**（或省略走轻门）；只有叙事明显要换类才改。禁止「有 L1 就默认 shop_ladder」
5. 口味/红线里的「禁止换物种；零件必须累计」**只约束** `same_object` / 玩家锁母体时；**不覆盖**「一组不同 X」或整表换货叙事

### B. `levels`

- 无整表参考：默认 **8**（L1–L8）；玩家只要六档 → `levels: 6`。
- 有整表格子参考：`levels` **跟格数**（允许 `6|8|9|12|15`）。禁止无视参考硬做成 8 再逐格刷。
- 门禁按 N 审，禁止为凑档硬编无意义补档。

### C. `delivery`

| 交付 | 含义 |
| :--- | :--- |
| `per_cell`（无整表信号时的**默认**） | 一档一张等大正方形；同框整梯只作体量预览，不是成品（MergePerCell） |
| `overview_sheet` | 关系门过后 **单次整表**；**最多重出 3 次**；满 3 次列缺陷停手。禁止从整表抠格冒充逐格成品 |

**何时强制 `overview_sheet`（可默认，不必再问）：** 整表格子参考；「整表 / 一起出 / 一次出齐 / 不要逐格 / 参考咋出就咋出」；多轨总览。

多轨（多张 L1）时：一个 yaml 多个 `tracks`；`overview_sheet` 可一行一轨。

## 风格（第一段写死一句，第二段照用。只取一条）

1. 玩家写下了风格，就用写下的。
2. **整表格子参考**（开场 0）：表面句写「软塑胶圆润厚实体 + 白圆角卡 + 深灰/炭黑底」等眼睛看见的；**出图垫参考文件**锁版式。不抄参考物件。
3. 单件风格参考、非整表：先跑 `python3 pmem_art.py ref-read <参考图路径>`，把看见的表面写成一句。`per_cell` 底写成「透明或纯黑隔离」；小高光不要写成油亮。不垫参考文件（除非锁 L1 外观）。不抄参考无关物件。
4. 风格和参考都没有：质感好的卡通可爱。圆润倒角、软阴影、饱和友好色，道具本身无脸，除非玩家要求有脸。

**底色闸**：
- `per_cell`：允许透明或纯黑隔离；禁止整格变成白/浅灰方卡底、相框 letterbox。
- `overview_sheet` 且参考是白卡深底图集：白圆角卡在深底上是版式，**允许**；禁止改成满幅白底或拆成单张白卡狂刷。

默认卡通下，产品实拍、油光不锈钢、真实木纹微细节要重扣。只有参考或 brief 明确写实才允许写实。

**域内红线（仍通用）**：糖果/甜品轨禁止默认焊进蛋糕、马卡龙、纸杯蛋糕（除非玩家点名蛋糕店链）。

## 第一段 · 升级链与画风（3 稿，先不出图）

固定 **3 稿**，不再拉到 8 稿。定清：链型、档数、交付、（若有）行列、升级链、画风一句。机读数字过了、合成说不通，仍然不算定稿；画风已经写成一句才能出图。3 稿仍说不通就停，一张图都不出。

每一稿先写 `chain_mode`（或注明轻门）/ `levels` / `delivery` / 可选 `grid_rows×grid_cols`，再写 N 行升级 + 一句画风。交给独立文本判断。没过只改未过行；已说通的锁住。

```bash
python3 pmem_art.py converge discuss --round <稿次> --prompt "<链型+N行>" --defects "<没过的是哪一行>" --next-fix "<下一稿只改哪几行>"
```

### 六条都要过（全链型）

1. 正好 `levels` 件，`level` 为 1..N 连续。同一任务域，不许串成同色杂物。
2. 每一档画面里将只有一件、居中（或整表中每格一件）。无脸，无等级字。
3. 两件相同的这一档合成下一档。下一档仍是一件，且说得出合成理由。换成同色无关物件，没过。
4. 体量只大一圈。低档占格大半，高档留边。末档最大。
5. 沿档位更复杂或物件类升级。轻门/`same_object` 看 `parts_add`；`shop_ladder`/`species_change` 看 `evolve_to`。只写「更华丽/加光/特效」没过。缩略图看不出的小饰片也算没过。
6. 相邻 `silhouette` 整句不能相同。  
   - `same_object`：必须 `base_body`，每档留母体词。  
   - `shop_ladder` / `species_change`：不写 `base_body`；禁止物件类回退；禁止无过渡的跨品类硬跳。  
   - 省略链型：`base_body` 可选；写了就粘住。

### 独立文本判断 · 五问（任一项「否」→ 改稿，不准出图）

1. 同店/同域吗？  
2. 有没有回退到更低档物件类？  
3. 有没有缺过渡的大跳档？  
4. 缩略图（约 64px）相邻档能分清吗？  
5. 升级理由具体吗？轻门/`same_object` 看 `parts_add`；`shop_ladder`/`species_change` 看 `merge_why`（不是「更高级/更华丽」）。

### 机读 yaml

讨论定稿后写成副本（勿改 canonical）。`tracks.<id>`：

- 推荐写：`chain_mode`、`levels`、`surface`；整表参考可写 `grid_rows` / `grid_cols`
- `same_object` 另加 `base_body`
- `rows[]`：`level` `name` `silhouette` `scale_delta` `scale_pct`  
  - 轻门 / `same_object`：`parts_add`（L1=`—`）  
  - `shop_ladder` / `species_change`：`evolve_to`、`merge_why`（L1 的 `merge_why` 可为 `—`）；`parts_add` 可 `—`

`scale_pct` 单调递增（建议 L1 ≥ 0.58，L8 ≤ 0.80；机读下限约 0.55 / 上限约 0.82）。

```bash
python pmem_art.py merge relation-judge --file <yaml> --all
```

**exit 0 才能出图。** 旧 canonical（无 `chain_mode`、八行、`parts_add`）仍应能过轻门。写成副本时不要改掉这份 canonical 里已有的 track。

**同范围重跑**（`same_object`）：`surface`、`base_body`、零件链从旧稿抄死；出图句每档重复母体 + 只加本档 `parts_add`。

## 出图

### `delivery=per_cell`（无整表信号时的默认）

关系过了 → 每一档单独出一张正方形 → `merge audit` → 可选 `normalize` 后再跑一次 audit → 第二段 converge（最多 4 轮，≥9.5）。  
同框不是交货（同框整梯只作体量预览）。每档首轮仍过 reasonableness review。不要把参考图文件垫进生图；不垫对方模型成图做「公平对比」。

### `delivery=overview_sheet`

关系过了 → **单次**生成整表：
- 有整表格子参考：垫该参考，行列与白卡深底跟参考一致；格内换题材。
- 有多张 L1：可垫 L1 锁第 1 列 / 各行首格。
- 按五问+链表验收。失败只改提示词重出，**累计 ≤ 3 次**；满 3 次停止并列出缺陷。  
禁止整表抠格当逐格成品。多模型对比时禁止把 A 模型整表垫进 B 模型参考。

## 第二段 · 美术（仅 per_cell）

最多 4 轮，≥9.5。表面句原样保留。关系散了或 audit 不过，美术分再高也不算过。

```bash
python pmem_art.py merge audit --dir <目录> --phase1 <yaml> --track <域名>
```

`converge generate` / `judge` / `finish` 记账。

## 禁止

- 没过 `relation-judge` / 五问就出图。
- 有整表格子参考或「一起出」却走 `per_cell` 逐格狂刷。
- 有整表参考却不数行列、不垫参考、硬做成默认 8 档。
- 「一组 X」未说同模加零件却默认 `same_object` 焊单母体。
- 用口味「禁止换物种」压过「一组不同 X」/ `species_change`。
- 未点名换货却默认锁 `shop_ladder`，或未选链型却强行锁 `base_body`。
- 玩家只要六档却硬凑八档无意义补档。
- `overview_sheet` 超过 3 次整表重出仍不停手。
- 从同框/整表抠图代替逐格交货（当 `delivery=per_cell` 时）。
- 公平对比时垫对方成图。
- `per_cell` 用白/灰卡底交差；或把整表参考拆成单张白卡狂刷。
- 糖果轨默认焊蛋糕/马卡龙/纸杯蛋糕。
