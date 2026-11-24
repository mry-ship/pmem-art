## 零点五、开画前强制 route（与总控同闸；点名 `/pmem-draw` 也要跑）

本技能**不能**绕开路由闸。标准路由句模板、冲突闸与 `execute_ok`/`ask` 语义见 `/pmem-agent` 第零段（此处不重写完整分流）。**任何自拟子合同或 `converge start` 之前**必须：

1. 把玩家原话收成一行标准路由句（模板见 agent）。
2. 跑：
```bash
python3 pmem_art.py route --text "<玩家原话>" --canonical "<标准路由句>"
```
3. 以 `route_ids` / `banner` 写入闸门缓存并锁定子合同；点名锁定不改判，仍须跑 route。
4. 缺缓存时可 `converge start --route-id draw.ordinary|draw.touchup|draw.clone|draw.key|…` **点名种闸**（与完整 route 等价放行）。
5. **禁止裸跳闸**：须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`；仅设 `PMEM_ART_SKIP_ROUTE_GATE` 不够。日常用 route 或 `--route-id` 点名种闸。
6. 点名锁定/口头草稿与 `route_ids` 冲突：停问玩家，禁止硬开画。
7. 判成界面 / 图标 / 合成梯：先留下本次 route 缓存，再读对应技能。

route 锁定后只读注册表该行的 **`pack_headings` 执行包**；不要整份全文串味。镜头包点选前不生图，仍须先 route。

你现在运行在 **pmem-art 闭环自评收敛生图模式**。进入普通图或原画后：**第 1 轮真实评分 ≥9.5 就立刻 finish**，禁止为凑轮次再画；不到线才进入下一轮，最多 3 轮兜底后交最高分并标明「未过线」。

## 执行卡 · 出图闭环（Agent 必读；细则见第二节）

1. `converge start`（缺缓存可 `--route-id` 点名种闸）→ Warm-Start 自动写入；会话写入 **理解合同 v1**（冻当前理解，不冻美术原句）。
2. 开跑后立刻写入四格：`python3 pmem_art.py contract set --id <session> --keep "…" --vary "…" --forbid "…" --spec "…" [--inferred "推断句"] [--defaults "默认：…" --vibe "…" --surface-fix "只改一处…"]`。四格不进路由句。`--vibe` 按风格优先级：①文字；②有文字+构图/整表参考→画风跟文字、垫图只锁版式；③无文字有风格参考→跟参考表面；④无参考仅题材文字→按文字推出；⑤都无→查 `COMMERCIAL_BENCHMARK` **按品类**填一句（仅 merge 品类钉 Gossip Harbor；禁止非 merge 套 Gossip Harbor 货柜）。Warm-Start 只注入已人工确认、且与四格不冲突的红线；候选红线和旧任务目标不进提示词。配方仍不进提示词。
3. 每轮续跑前先读最小工作集：`python3 pmem_art.py contract working-set --id <session>`——只用合同+本图+单点改嘱，**禁止**靠长聊天重谈 L0/L1。
4. 画师新反馈先归层：`python3 pmem_art.py contract classify --text "…"`；再 `contract patch --id <session> --feedback "…"`。L0=可能换交付/重开；L1=升锁点；L2=只改一处。
5. 首轮 generate 前：`reasonableness review`（`--draft` + `--revised` + checklist）过闸。
6. 出图顺序（禁 stub）：`converge generate --emit-prompt` 打印「最终 Prompt」→ GenerateImage 逐字用该句 → `converge generate --image <path>` 登记（可省 `--prompt` 复用 pending）。`converge generate` **自动并入** Warm-Start；打印 `WARM_START_MERGED=1|0` 与 `FINAL_PROMPT_SHA1=`。禁止另写 brief、禁止手贴 Warm-Start、禁止占位图骗闸。垫图只用该轮打印的那一张：默认是最初参考，改点只写进提示词；只有打印写明垫第几轮成图时，才垫那张成图。
7. 看图打六维 → `converge judge`；≥9.5 到线即 `finish`；不到线最多 3 轮；交件标明是否过线。本项目已开安全早停：掉分/平台 → 交历史最高分，见停机码立即 `finish`。
8. 风格优先级同第 2 条；都无才查 `benchmark lookup` / `COMMERCIAL_BENCHMARK.md`（**按品类**；仅 merge 钉 Gossip Harbor）；**禁止**把 benchmarks 目录图当垫图（start/generate 双闸）。
9. 禁止裸 `--skip-route-gate`（须 `PMEM_ART_ALLOW_GATE_SKIP=1` + `--skip-reason`）。会话命令一律显式 `--id`。

## 合同 · 变体

只在类型是变体时执行。轮次用第二节的 `converge generate` / `judge` / `finish`。先 `python3 pmem_art.py search --module <父模块>`，锁住不能改的人设：发色、瞳色、标志配饰、主色板。

- 换画风：另建子模块（如 `character.Astra.Chibi`）。不垫旧画风原图，人设只写进提示词。
- 表情或动作差分：几张写死几张。每一轮垫最初的角色原图，修正只写进提示词。锁五官比例和机位。单张表情只交付这一张。
- **局部表情硬验收（困倦/半眯/眨眼等）**：`next_fix` 与 defects 必须写可量测部位（如上眼睑是否压到虹膜中线、单眼是否闭合）。成图上该部位没兑现，风格分再高也不能停；禁止只靠「更困一点」空话抬分。风格维应保持 ≥8.5，不要为改表情把画风打崩到 6 档。

然后按上面的 3 轮、≥9.5 闭环生图。完成后 `python3 pmem_art.py ingest <新图路径> -p "<含角色名和画风或差分的提示词>" --apply`。

## 交件可见（出图结算 · Agent 必读）

**硬规矩**：只要本趟交了图（闭环任一轮、终稿、拆层散图、审图对象、锁风样张、归档清单等），结算必须先贴一张 Markdown **可点单图表**，再对表内每一张 `Read` 贴进对话。禁止只列文件名、禁止只交拼板/HTML、禁止「路径在目录里自己点」。

链接格式：相对仓库根，形如 `[第2轮](.memory-art/converge/boards/<id>/images/r2.jpg)` 或 `[01-bg](assets/<job>/new/01-bg.png)`。表头按交付类型选列，至少含「名称/槽位」+「可点图」。

### 闭环出图（跑过 `converge`）
1. **过程图拼板**：Read `process_sheet.jpg` 贴进对话。
2. **轮次单图表**：贴 finish 打印的表（轮次 × 分数 × 可点图）；也可用 `rounds.md`。
3. **逐张 Read**：表里每一轮原图各 Read 一次。
4. **本次耗时**：finish 报告末行「本次耗时」原样写出。
5. **中途每轮**：每次 `judge` 后立刻贴/更新可点表（至少本轮一行）并 Read 本轮原图；不要等 finish 才第一次给可点单图。

禁止只交拼板。禁止只甩 HTML。

### 四格与防污染（执行时必读）
四格不进路由句。必须保持、可以变化、明确禁止、交付规格只写 `contract set --keep --vary --forbid --spec`，标明原话或推断。禁止写入 `--canonical`。普通图用「题材不变」，禁止写「不换题材」。合同里的升级、一组、多张不得改技能。首轮提示词和后续修改只服从四格；聊天不是第二份需求；用户改口就用最新原话重写四格。
记忆只辅助。当前原话和四格优先于历史记忆。候选红线、没写 trust 的条目、旧任务主体、构图、档序和完整提示词不进提示词。已确认红线去掉旧任务目标，与明确禁止冲突则排除。研发 `.memory` 不进美术提示词。界面不继承合成梯玩具货柜缺省。
未点名接续只垫 `assets/refs/`、`downloads/`、`assets/skill_*/refs/`。禁止垫 out、phase1、关系稿、`.memory-art/converge` 过程板。垫图只取样式；只有用户说优化这张图才写原图不足。双参考像素同框仍硬停。最多 3 轮。

### 非闭环多图（拆层 / 审图 / 锁风样张 / 归档等）
同样强制可点单图表 + 逐张 Read。拆层须含叠回整图、幽灵对比、全部 `new/*.png`（有 `layers.md` 直接贴）。纯文字交付（提示词、无附图教练）不必出表。

---

## 记忆静默 / 履历可见（Agent 必读）
- `converge finish` 后系统**自动**写反思、更新 `taste.json`、强化 recipe/红线、悄悄排队 1–2 条知识建议——**无需**再跑 `/pmem-coach`。
- 对用户默认展示见「交件可见」：必出**可点单图表** + Read 每一张图 +（闭环时）拼板与**本次耗时**。HTML 过程板只是旁路。记忆写入不要旁白。
- 用户要安静出图时用 `--quiet` 或说「只要终稿」。想看进步、短板或知识卡时再用 `/pmem-coach`。