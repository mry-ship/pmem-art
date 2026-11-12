## 零点五、开画前强制 route（与总控同闸；点名 `/pmem-draw` 也要跑）

本技能**不能**绕开路由闸。标准路由句模板、冲突闸与 `execute_ok`/`ask` 语义见 `/pmem-agent` 第零段（此处不重写完整分流）。**任何自拟子合同或 `converge start` 之前**必须：

1. 把玩家原话收成一行标准路由句（模板见 agent）。
2. 跑：
```bash
pyw -3 -u pmem_art.py route --text "<玩家原话>" --canonical "<标准路由句>"
```
3. 以 `route_ids` / `banner` 写入闸门缓存并锁定子合同；点名锁定不改判，仍须跑 route。
4. 缺缓存时可 `converge start --route-id draw.ordinary|draw.clone|draw.key|…` **点名种闸**（与完整 route 等价放行）。
5. **禁止裸跳闸**：须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`；仅设 `PMEM_ART_SKIP_ROUTE_GATE` 不够。日常用 route 或 `--route-id` 点名种闸。
6. 点名锁定/口头草稿与 `route_ids` 冲突：停问玩家，禁止硬开画。
7. 判成界面 / 图标 / 合成梯：先留下本次 route 缓存，再读对应技能。

route 锁定后只读注册表该行的 **`pack_headings` 执行包**；不要整份全文串味。镜头包点选前不生图，仍须先 route。

你现在运行在 **pmem-art 闭环自评收敛生图模式**。进入普通图或原画后：**第 1 轮真实评分 ≥9.5 就立刻 finish**，禁止为凑轮次再画；不到线才进入下一轮，最多 4 轮兜底后交最高分并标明「未过线」。

## 执行卡 · 出图闭环（Agent 必读；细则见第二节）

1. `converge start`（缺缓存可 `--route-id` 点名种闸）→ Warm-Start 自动写入；会话写入 **理解合同 v1**（冻当前理解，不冻美术原句）。
2. 开跑后立刻补可见默认：`pyw -3 -u pmem_art.py contract set --id <session> --defaults "默认：…" [--locks "…" --unlocks "…" --vibe "…" --surface-fix "只改一处…"]`。`--vibe` 按风格优先级：①文字；②有文字+构图/整表参考→画风跟文字、垫图只锁版式；③无文字有风格参考→跟参考表面；④无参考仅题材文字→按文字推出；⑤都无→查 `COMMERCIAL_BENCHMARK` **按品类**填一句（仅 merge 品类钉 Gossip Harbor；禁止非 merge 套 Gossip Harbor 货柜）。
3. 每轮续跑前先读最小工作集：`pyw -3 -u pmem_art.py contract working-set --id <session>`——只用合同+本图+单点改嘱，**禁止**靠长聊天重谈 L0/L1。
4. 画师新反馈先归层：`pyw -3 -u pmem_art.py contract classify --text "…"`；再 `contract patch --id <session> --feedback "…"`。L0=可能换交付/重开；L1=升锁点；L2=只改一处。
5. 首轮 generate 前：`reasonableness review`（`--draft` + `--revised` + checklist）过闸。
6. `converge generate` **自动并入** Warm-Start `prompt_block`；会话写 `warm_start_merged=true` 并打印 `WARM_START_MERGED=1|0`，以及「装配句 / Warm-Start 段 / 最终 Prompt」。**调用 GenerateImage（或外部生图）必须用「最终 Prompt（出图须用这句）」**，禁止另写一份、禁止手贴 Warm-Start；不要用「GenerateImage Hook 有没有跑」判断是否并入。
7. 看图打六维 → `converge judge`；≥9.5 到线即 `finish`；不到线最多 4 轮；交件标明是否过线。
8. 风格优先级同第 2 条；都无才查 `benchmark lookup` / `COMMERCIAL_BENCHMARK.md`（**按品类**；仅 merge 钉 Gossip Harbor）；**禁止**把 benchmarks 目录图当垫图（start/generate 双闸）。
9. 禁止裸 `--skip-route-gate`（须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`）。

---

## 合同 · 多图分工

只在类型是多图分工时执行。不走 `low` / `medium` / `high` / `recompose`。四档只留给一张图的普通图和原画。

每张图必须有一个分工：机位、身份、状态、画风、版式。定稿里没写分工的图不垫。一次交来两张图时，先看它们各管什么，不要并成一张参考再画。

交付张数按定稿写死：一张拼板，或每个状态各一张。每个交付物 **最多4轮、≥9.5到线即停**（CLI `max_rounds=4`）；finish 时必须标明「过线/未过线（≥9.5）」；分工问题写在评分里，到线即停、不鼓励凑满。定稿写了拼板，验收看两态的转角和侧壁宽度。定稿写死底：实色、场景，或「透明意图」（Cursor → 不透明隔离底，禁止后抠；gpt-image 等 → 真 alpha PNG）。品红块和品红底 JPG 不能当交付。

- **第一态**：身份图和结构图都垫上。身份图原来的机位作废，机位以结构图为准。开会话用 `converge start --contract split`，不要写 `--scale medium`。
- **下一态**：只垫上一态交件。交件是已经 ≥9.5 的那张，或满 4 轮里分最高的那张。过线只认 ≥9.5；没过线的最高分不得标成通过，但仍然是下一态唯一垫图。不要因为上一态未过线就停掉下一态。锁机位和身份，只改这个状态。转角和侧壁宽度跟上一张一致。
- **开关态状态机（硬锁）**：开盖须铰链可见；挂锁须解锁/打开/移除；扣环与锁鼻应对得上；禁止「盖已开但仍挂闭合挂锁」。金币等填充物禁止互穿粘连。合理性闸 `state_machine` 不过不许 generate；checklist 须含 `role_separation=ok;state_machine=ok`。
- 生图接口一次只能垫一张时，停下来说明。不要把结构图只写进文字里，就算垫过。定稿要求两张参考的像素同时出现在同一张成图里时，停下来说明原因，不开始出图，也不改派到别的合同。
- 一组道具、同一画风、彼此不升级：每件一张，都垫同一张风格图，身份各写各的。合成关系仍走合成梯。
- 同一地点的远景、中景、近景：每张锁一个景别，场景身份垫同一张，三张都交。镜头包仍是先给方案、点一套再画。

点名部位没达到，或锁住的邻区被整张重画洗掉，9.50 也不能停。嘴、眼、手、提梁、信纸这类点名锁，每一轮生成词都要带上；优点里没单独写明守住，或缺陷仍点到它，本轮不能过线。打分前把成图和每一张分工图并排看。不能只看垫进去的那一张。

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**参考图分析 + 每轮六维与总分 + 可点开的过程板 + 总结**；记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看进步、短板或知识卡时再用 `/pmem-coach`。