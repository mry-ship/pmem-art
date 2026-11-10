---
name: pmem-merge-ladder
description: 玩家要一条同域合成升级梯，或生图分流判成合成梯时使用。只有 /pmem-merge-ladder：先文字定链型与升级关系，再说通再出图。同族形变（主流）走 shop_ladder；同模加装才 same_object；乐器整表走 species_change。merge 默认就是一组：delivery=overview_sheet、levels=8；有格子参考跟格数与版式；玩家点名档数跟点名；仅当玩家明确说一档一张/逐格/单张时才走 per_cell。
---

# `/pmem-merge-ladder` — 同域合成梯

## 底与透明度（按生图引擎 · Agent 必读）
- **Cursor `GenerateImage` 不支持真透明**。口语要「透明底」时，改写为**不透明隔离底**（默认纯黑 `#000000`，或定稿写死的实色空底）；交不透明 PNG/JPG 即可。**禁止**成图后再抠色、抠角、本地挖洞冒充 alpha。**例外：合成梯整表（overview_sheet）用浅色圆角卡，纯黑只给 per_cell。**
- **第三方支持透明的引擎**（如 `gpt-image` / 明确带 alpha 的 API）：可**直接**生成真 alpha PNG；白底/品红底不算透明底。
- 结算时写清用的是哪类底：`true_alpha` 或 `opaque_isolation`。默认出图路径是 Cursor 时，不要为了凑 alpha 去跑 `export_mode_c_icon` 抠图。

## 怎么用
```text
/pmem-merge-ladder 一组建筑；chain_mode=shop_ladder
/pmem-merge-ladder 青瓷药瓶同物件八档；chain_mode=same_object
/pmem-merge-ladder [附格子参考] 一组乐器；参考咋排就咋出
/pmem-merge-ladder 青瓷药瓶八档；一档一张正方形
```
默认整表一次出齐。有附图先认是不是整表格子。细则透镜见 `docs/MERGE_MULTI_LENS.md`；Gossip Harbor 专属见 `docs/GOSSIP_HARBOR_MERGE.md`；多游戏真链档序见 `docs/MERGE_CHAIN_REFERENCE.md`。

## 执行卡
1. 定 `chain_mode` / `levels` / `delivery`（默认 overview_sheet、常 8；有格子参考跟格数；仅点名逐格才 per_cell）。
2. 关系稿最多 2：五问 + `relation-judge` + 对标档序 + `surface` 一句；说不通不出图。
3. 风格：有文字跟文字；没写风格钉 Gossip Harbor 货柜（整表参考只锁格子）；点名写实/水彩等才离开。禁止垫竞品图。
4. 整表最多 4 轮、≥9.5 到线即停；逐格各档并行。会话 id 显式，禁默写 `latest`。

## 开场
- 整表格子参考 → 数行列、`delivery=overview_sheet`、垫参考锁版式；无文字风格时画风钉 Gossip Harbor。
- 无格子、垫图是竖屏商店图 → 整表 **4×2**、`--aspect-ratio 9:16`；横表垫图才用 2×4。
- 无格子参考也不回落逐格；默认仍 overview_sheet + levels=8。

### 链型
| 链型 | 何时 | 硬约束 |
| :--- | :--- | :--- |
| `same_object` | 同模加装 | 必须 `base_body`；`parts_add` 累计可读 |
| `shop_ladder` | 同族/同店升级（主流） | 不写 `base_body`；`evolve_to`+`merge_why` |
| `species_change` | 同域换物种（乐器整表等） | 同 shop；乐器/船柜优先 |
| （省略） | 非糖果未点名 | 轻门：件数、剪影不复读、`parts_add` 具体 |

糖果/同店升级默认可 `shop_ladder`；非糖果未点名禁默锁 shop_ladder。家族=店域/色相，不是纹样贯穿。

### 升级合同（硬）
- 每档一件完整货；前段朴素，后段才出配料/犒赏。
- **邻档至少变一项**：剪影 / 件数 / 容器 / 完成态。中段同杯加碟、加糖勺、换花纹**合法**，只要缩略可分。
- 禁止只靠「同形放大」或「全程只堆饰片、八档都不换容器/完成态」撑满；也禁止为避加件而每档硬换物种（浇水焊轮子、果酱跳无关糊团）。
- 体量提示：可接近持平，不要求单调放大；硬伤仅「末档明显矮于前档」「邻档剪影句相同」。
- **禁止跨轮抠格拼表**凑体量阶梯（残片/切顶一律不过）。
- 对标写真链档序；点名 GH 时档序见 `docs/GOSSIP_HARBOR_MERGE.md`，勿把别家档序写进本链。

### levels / delivery
- levels 默认 8，对标后可改为 6|8|9|12|15；有格子跟格数。
- overview_sheet 默认；仅「一档一张/逐格/单张」才 per_cell。

## 风格与底（只写一处）
1. 有文字风格 → 跟文字（整表参考仍可垫锁版式）。
2. 有参考无文字 → `ref-read` 取样式写 `surface`；整表参考无文字时仍钉 Gossip Harbor，参考只锁格子。
3. 都无 → Gossip Harbor **玩具货柜卡通**写入 `surface`（光泽卡通 3D、圆润厚实、糖釉玩具高光、棋盘缩略可认）。
- **surface 必禁**：写实摄影、美食棚拍、产品静物、玻璃真实折射、木纹指纹、果汁乳浊摄影感、微距毛孔。只写「Gossip Harbor」四字不够，必须带玩具货柜+禁写实硬句。
- **overview_sheet 默认浅色圆角卡**（浅蓝/奶油浅底），禁止默用纯黑整表底（黑底留给 per_cell 隔离）。
- per_cell：Cursor 纯黑/实色隔离；透明引擎可真 alpha。禁止后抠。

## 第一段 · 关系（最多 2 稿）
写死：对标链+档序、过程类型、`chain_mode`、`levels`、`delivery`、N 行升级、`surface`。

### 五问（否→改稿）
1. 同店/同域？家族是店域非纹样？对标是真档序？
2. 有无回退 / 无过渡大跳 / 另链城堡焊末档？
3. 64px 邻档可分？L1 是否过满、犒赏是否过早？
4. 升级理由具体？（parts_add / merge_why，不是「更华丽」）
5. 邻档是否至少变了剪影/件数/容器/完成态之一？中段加件是否可读？合两下能否倒推？

### 机读
```bash
pyw -3 -u pmem_art.py merge relation-judge --file <yaml> --all
```
exit 0 才能出图。`scale_pct` 可不单调；邻档 `silhouette` 整句禁相同。

## 出图提示词模板（GenerateImage 必用）
统一前缀（整表锁死）+ 每格一句短描述：
```text
<surface 一句：Gossip Harbor 玩具货柜卡通，糖釉卡通道具，禁写实/棚拍/折射/木纹>。整表统一：同一 3/4 俯视、同一柔光左上、浅色圆角卡、同色相家族；每格一件居中留边；无字无脸。
L1 <短名>：<剪影/容器/完成态一句，用玩具材质词，勿写摄影级质感>
L2 …
（按 levels 列完）
禁止跨格拼贴、残片、切顶；邻档靠剪影或件数可分，不靠放大。
禁止美食棚拍、产品静物、玻璃真实折射、木纹指纹、果汁乳浊摄影感。
```
有格子参考：垫参考锁行列与卡底，格内换题材。无参考竖屏：4×2 + 9:16。

## 出图闭环
```bash
pyw -3 -u pmem_art.py converge start --session <merge_id> --goal "merge overview_sheet：…" --module <模块> --route-id merge.ladder
pyw -3 -u pmem_art.py reasonableness review --id <merge_id> --skill merge --draft "…" --revised "…" --checklist "subject_action=ok;element_budget=ok;hard_locks=ok;fail_at_glance=ok;single_centered_item=ok;chain_mode_declared=ok;upgrade_reason_concrete=ok;family_or_base_lock=ok;sheet_safe_zone=ok"
pyw -3 -u pmem_art.py converge generate --session <merge_id> --round <N> --image <sheet> --prompt "<模板修订句>"
pyw -3 -u pmem_art.py converge judge --session <merge_id> --round <N> --image <sheet> --dims "构图9.0/光影9.0/透视9.0/质感9.0/风格9.0/无瑕疵9.0" --defects "…" --next-fix "…"
pyw -3 -u pmem_art.py converge finish --session <merge_id>
```
per_cell：各档并行独立 session；`merge audit` 验收。

### 整表验收清单
- [ ] 超框/切顶：整件落在浅色圆角卡内并留边
- [ ] 邻档：64px 靠剪影或件数可分（不要求框高递增）
- [ ] **拼贴 / 残片 / 切顶**：无跨轮抠格拼接痕迹
- [ ] 眼睛：生物链可读；道具默认无脸
- [ ] 版式：浅色圆角卡（有参考跟参考）；无等级字；一格一件
- [ ] 关系：五问仍通；无回退/大跳

## 禁止
- 没过 relation-judge / 五问就出图；未点名逐格却 per_cell 狂刷。
- 跨轮抠格拼表；用体量阶梯脚本硬凑框高。
- 把「禁止只靠堆料撑满」误读成中段不许加件。
- 整表默用纯黑底；糖果轨默认焊蛋糕/马卡龙/纸杯蛋糕。
- 已到线或满 4 轮仍狂刷；点名逐格却串行。
