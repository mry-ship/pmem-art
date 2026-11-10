## 执行卡 · 合成梯（Agent 必读；细则见后文）

1. 先定 `chain_mode` / `levels` / `delivery`（默认 overview_sheet、常 8；有格子参考跟格数；仅点名逐格才 per_cell）。
2. 关系稿最多 2：五问 + `relation-judge` + 商业对标档序 + `surface` 一句；说不通不出图。
3. 风格优先级：①有文字跟文字（有整表参考时垫图**只锁版式**，不锁参考画风）；②有参考无文字跟参考表面；③无参考仅题材/链型文字则按文字推出；④都无才 `benchmark lookup --category merge`（默认钉 Merge Mansion）写入 surface；**禁止**垫 benchmarks/ 竞品图。
4. 整表：`converge` 最多 4 轮、≥9.5 到线即停；逐格：各档并行独立 session。
5. 会话 id 显式；discuss/generate 禁默写 `latest`。

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
- `overview_sheet` / `per_cell` 已到线或已满4轮仍继续狂刷。
- 关系第 1 稿已过仍空写凑满 2 稿；或已到线仍硬凑满 4 轮。
- 结构/关系硬伤后仍垫失败整表叠轮。
- 点名逐格却串行等完一档再开下一档（须并行）。
- 商业诊断再连刷整表（只打字）。
- 未点名 Dark/Tinted 却宣称 App Icon 三态已派生齐套。
- 从同框/整表抠图代替逐格交货（当 `delivery=per_cell` 时）。
- 公平对比时垫对方成图。
- `per_cell` 用白/灰卡底交差；或把整表参考拆成单张白卡狂刷。
- 糖果轨默认焊蛋糕/马卡龙/纸杯蛋糕。