---
description: 【最多1枪】局部改快通道：成图只拧点名处（pmem-art）
---

# `/pmem-touchup` — 局部改（成图快修）

**路由以 CLI 为准。** 点名 `/pmem-touchup` 也要先跑 `route`，确认 `route_ids` 含 `draw.touchup`。本技能只做快修：默认最多 1 枪交件，可选第 2 枪，不走三轮闭环，不拼履历板。

## 零点五、开画前 route

1. 把玩家原话收成一行标准路由句（模板见 `/pmem-agent` 第零段）。
2. 跑：`route --text "<玩家原话>" --canonical "<标准路由句>"`。
3. 缺缓存时可 `converge start --route-id draw.touchup` 点名种闸。禁止裸跳闸（须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`）。
4. `route_ids` 不含 `draw.touchup`（换题材 / 换机位 / 整图重做）：停，改走 `/pmem-draw`，不要硬走本通道。

## 合同 · 局部改

只在类型是**局部改**（`draw.touchup`）时执行。目标：成图已经大体合格，只拧点名小处——**要快**，禁止伪装成普通图三轮闭环。

### 硬闸
- **必须有待改成图**（玩家附图 / 刚交的终稿 / 明确路径）。goal 写清「继续这张 / 修这张 / 局部改」。
- **锁**：机位、身份、题材、整构图、未点名区域。
- **四格不进路由句**。局部改的保持项和禁止项写入 `contract set`，不写进标准路由句。
- **只改**：玩家点名的部位或瑕疵（可另垫一张局部参考说明目标质感/造型）。
- **打回正式技能**：重做 / 换题材 / 换机位 / 整脸表情差分 / 合成梯某档重画 → 不要硬走本通道。

### 快流程（最多1枪默认交；可选第2枪）
1. 已跑零点五 `route`，确认 `route_ids` 含 `draw.touchup`。
2. `converge start --id <sid> --route-id draw.touchup --scale low --max-rounds 2 --ref-image "<待改成图>" --goal "继续这张；局部改：<点名部位与改法>"`  
   （可再加局部参考进 `--reference-image-paths`；会话会自动跳过正式合理性闸、标 touchup。）
3. `converge generate --id <sid> --emit-prompt` → GenerateImage **必须垫待改成图**（描述写死：未点名区域保持不变，只改点名处）→ `converge generate --id <sid> --image <path>`。
4. **默认人眼过就 `finish --quiet`（最多1枪即交）**。不要为凑 ≥9.5 再画；不要拼三轮履历板（交成图路径即可）。仅玩家说「不够 / 再修一点」才开第 2 枪（仍锁同一成图与点名范围）。
5. 轻记反馈可用：`feedback "<原话>" --module <模块> [--asset <成图>]`；禁止当新开普通图交付交差。

### 提示词要点
- 首句点名「edit / 局部修改这张图」。
- 列清：改什么、改成什么样；若有局部参考，写「仅该部位跟参考」。
- 写死否定：不改机位、不换身份、不重构图、不改未点名区域。
