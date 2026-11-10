## 零点五、开画前强制 route（与总控同闸；点名 `/pmem-draw` 也要跑）

本技能**不能**绕开路由闸。标准路由句模板、冲突闸与 `execute_ok`/`ask` 语义见 `/pmem-agent` 第零段（此处不重写完整分流）。**任何自拟子合同或 `converge start` 之前**必须：

1. 把玩家原话收成一行标准路由句（模板见 agent）。
2. 跑：
```bash
python3 pmem_art.py route --text "<玩家原话>" --canonical "<标准路由句>"
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
2. 开跑后立刻补可见默认：`python3 pmem_art.py contract set --id <session> --defaults "默认：…" [--locks "…" --unlocks "…" --vibe "…" --surface-fix "只改一处…"]`。`--vibe` 按风格优先级：①文字；②有文字+构图/整表参考→画风跟文字、垫图只锁版式；③无文字有风格参考→跟参考表面；④无参考仅题材文字→按文字推出；⑤都无→查 `COMMERCIAL_BENCHMARK` **按品类**填一句（仅 merge 品类钉 Merge Mansion；禁止非 merge 套软塑胶）。
3. 每轮续跑前先读最小工作集：`python3 pmem_art.py contract working-set --id <session>`——只用合同+本图+单点改嘱，**禁止**靠长聊天重谈 L0/L1。
4. 画师新反馈先归层：`python3 pmem_art.py contract classify --text "…"`；再 `contract patch --id <session> --feedback "…"`。L0=可能换交付/重开；L1=升锁点；L2=只改一处。
5. 首轮 generate 前：`reasonableness review`（`--draft` + `--revised` + checklist）过闸。
6. `converge generate` **自动并入** Warm-Start `prompt_block`；会话写 `warm_start_merged=true` 并打印 `WARM_START_MERGED=1|0`。外部生图以 generate 吐出的 prompt 为准，**不要**用「GenerateImage Hook 有没有跑」判断是否并入。
7. 看图打六维 → `converge judge`；≥9.5 到线即 `finish`；不到线最多 4 轮；交件标明是否过线。
8. 风格优先级同第 2 条；都无才查 `benchmark lookup` / `COMMERCIAL_BENCHMARK.md`（**按品类**；仅 merge 钉 Merge Mansion）；**禁止**把 benchmarks 目录图当垫图（start/generate 双闸）。
9. 禁止裸 `--skip-route-gate`（须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`）。

---

## 合同 · 变体

只在类型是变体时执行。轮次用第二节的 `converge generate` / `judge` / `finish`。先 `python3 pmem_art.py search --module <父模块>`，锁住不能改的人设：发色、瞳色、标志配饰、主色板。

- 换画风：另建子模块（如 `character.Astra.Chibi`）。不垫旧画风原图，人设只写进提示词。
- 表情或动作差分：几张写死几张。每一轮垫最初的角色原图，修正只写进提示词。锁五官比例和机位。单张表情只交付这一张。
- **局部表情硬验收（困倦/半眯/眨眼等）**：`next_fix` 与 defects 必须写可量测部位（如上眼睑是否压到虹膜中线、单眼是否闭合）。成图上该部位没兑现，风格分再高也不能停；禁止只靠「更困一点」空话抬分。风格维应保持 ≥8.5，不要为改表情把画风打崩到 6 档。

然后按上面的 4 轮、≥9.5 闭环生图。完成后 `python3 pmem_art.py ingest <新图路径> -p "<含角色名和画风或差分的提示词>" --apply`。

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**参考图分析 + 每轮六维与总分 + 可点开的过程板 + 总结**；记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看进步、短板或知识卡时再用 `/pmem-coach`。