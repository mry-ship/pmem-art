# EXEC PACK draw.key

banner heading: ## 合同 · 原画
skill: pmem-draw
file: .cursor/skills/pmem-draw/SKILL.md

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
2. 开跑后立刻补可见默认：`python3 pmem_art.py contract set --id <session> --defaults "默认：…" [--locks "…" --unlocks "…" --vibe "…" --surface-fix "只改一处…"]`。缺风格气质写进 `--vibe`。
3. 每轮续跑前先读最小工作集：`python3 pmem_art.py contract working-set --id <session>`——只用合同+本图+单点改嘱，**禁止**靠长聊天重谈 L0/L1。
4. 画师新反馈先归层：`python3 pmem_art.py contract classify --text "…"`；再 `contract patch --id <session> --feedback "…"`。L0=可能换交付/重开；L1=升锁点；L2=只改一处。
5. 首轮 generate 前：`reasonableness review`（`--draft` + `--revised` + checklist）过闸。
6. `converge generate` **自动并入** Warm-Start `prompt_block`；会话写 `warm_start_merged=true` 并打印 `WARM_START_MERGED=1|0`。外部生图以 generate 吐出的 prompt 为准，**不要**用「GenerateImage Hook 有没有跑」判断是否并入。
7. 看图打六维 → `converge judge`；≥9.5 到线即 `finish`；不到线最多 4 轮；交件标明是否过线。
8. 缺风格：查 `python3 pmem_art.py benchmark lookup --category <品类>` 或 `docs/COMMERCIAL_BENCHMARK.md` 填一句；**禁止**把 benchmarks 目录图当垫图（start/generate 双闸）。
9. 禁止裸 `--skip-route-gate`（须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`）。

---

## 合同 · 原画

只在类型是原画时加在闭环上。闭环轮次、9.5、评分履历与上面相同。

提示词用完整句子，不要纯 tag。顺序：主体与动作，场景，光影与时段，材质与画风，色板，景别画幅。排斥项写成正向句（「干净的青瓷白与墨蓝，无霓虹」）。每轮用上一轮的具体缺陷重写整句，仍禁止只堆负向 tag。无玩家画风 / 无风格样张时：画风句必须写成**同品类顶级商业 Key Art / 上架主视觉气质**（空气透视、主视觉记忆点、商业完成度用具体名词），禁止空喊「史诗好看」或回落泛插画。**仅当题材是软糖/半透明糖果介质时**：修订句须写半透明 SSS、宽柔高光、边缘暖散射，并禁止硬塑胶/油镜高光；金器/木箱/陶瓷等非软糖题材勿套这条。要几套构图自己挑，改走镜头包，点选前不生图。

**硬闸 · 有风格样张时（layout_not_style_echo）**：只借色板 / 光影 / 媒介 / 笔触，**禁止**继承样张的机位、主体占比、前景道具摆位、左右分区。成图构图一眼能对上样张分区或同一机位 → 构图维压到 ≤8.5 且本轮不可停；禁止用「大体像风格」软过。合理性闸 checklist 必须标 `layout_not_style_echo=ok`。

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**参考图分析 + 每轮六维与总分 + 可点开的过程板 + 总结**；记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看进步、短板或知识卡时再用 `/pmem-coach`。