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

## 合同 · 克隆

只在类型是克隆时执行。轮次用第二节的 `converge generate` / `judge` / `finish`，最多 4 轮，合格线 ≥9.5。不要按第一节继承参考构图。禁止无六维数字宣称通过。默认锁大约 95% 的画风，换的是题材。

- **没有参考**：只靠 brief 和自写风格圣经。媒介必须在 brief 里写明。
- **有参考**：每一轮都垫最初那张风格参考。比例、眼型、描边、文案的修正写进提示词，不要垫上一轮成图。禁止事后拿无关图当原图对照。

**锁**：媒介、色板角色、光感、材质语法、红线。按类再加：

- 场景 / 原画：锁媒介和光感，构图可以换。
- **界面弹框母版**：锁媒介和双层描边（参考有两层就把两层都锁住）。新题材是空内容的九宫格面板：中心大块留白，角区不放复杂纹样。禁止把参考里的道具（如礼盒）放进内容区。顶栏纹样最多 1 个。底栏只用符号钮。没有 brief 就不造可读界面文字。参考若是道具图标，分析里写明「只借材质描边，不借布局和主体」。整套组件仍走 `/pmem-ui`，克隆只交一张母版。内容区回声了参考主体 → 压分并且不可停。
- 图标：锁外框、材质、背景习惯。主体是新的。纹样最多 1 个。缩略轮廓要清楚。搪胶、软塑胶体积只在参考本身是玩具或 Q 版时才写。
- 角色：脸的画法跟参考媒介。通用只锁双眼分穴、虹膜、巩膜月牙、高光，禁止独眼和黑点瞳。软颊、短粗肢、大头桶身只在卡通或 Q 版参考里才写。换装可以，禁止三视图。角色身份不是名人脸或著名服装。

**不锁**：构图、题材、身份，除非玩家要求保留。尺寸按玩家说的来，否则跟参考。

风格圣经从参考像素归纳媒介、色板、描边。参考是道具图标时，禁止把道具外形写进界面 brief。界面 brief 写清空内容弹框、禁止中心纹样、符号钮。

六维是 `构图/光影/透视/质感/风格/无瑕疵`。构图分同时看有没有把参考题材抄回来。缺陷写了抄回参考主体、礼盒进了内容区，压到 8.85 以下并且不能停。≥9.5 且结构门过了才停。主参考是黑点瞳而合同要虹膜时，写死虹膜，禁止为了贴参考改回黑点眼。克隆只垫风格那一张。另一张锁机位或身份时，改走多图分工。

交付时对照的是这趟真正垫过的参考。

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-coach`。
- 对用户默认展示：**参考图分析 + 每轮六维与总分 + 可点开的过程板 + 总结**；记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看进步、短板或知识卡时再用 `/pmem-coach`。