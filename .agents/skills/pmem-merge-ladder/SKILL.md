---
name: pmem-merge-ladder
description: 【截图可见·必读】merge-2 棋盘进阶梯（默认L1–L8）。同任务域。优先整梯一次出 sheet；≥9.6。无参考默认卡通可爱（Mode A 必写 vinyl/chibi stub）；有参考跟参考 medium。稳测连续3组过线。
---

# `/pmem-merge-ladder` — Merge-2 棋盘进阶梯（整梯优先 · ≥9.6）

> **合格线 `≥ 9.6 / 10.0` · 最多 8 轮 · 禁止无五维数字宣称 PASS**。  
> **优先：一次生成整梯 contact sheet（L1…LN 同框），再切格评分**。某格反复塌身份才可单格补生（同品牌胶/光照）。

Default N=**8**。Modes：A 零参考 · B 单参考风格 · C 参考整梯（抄域纪律+medium，不抄 motif）。

## 硬：升级路径
1. 同一任务域（禁同色杂物串）
2. 订单价值递增
3. 棋盘完整图标：居中、缩略可读；无脸；无等级字
4. 相邻档缩略差：体量/零件/身份可辨；同模只加特效=失败
5. 同族放大必须可读（缩略 ≥~1.6× 体量或明显更多零件）

### 类
| 类 | 规则 |
|---|---|
| category-swap | 域内换完整道具 + 品牌胶 + 体量升 |
| family-morph | 同物长大/零件↑ |
| theme-morph | 主题内身份跳但用途一致且规格升 |

Banned：跨域杂物串；同瓶叠光；纯 FX；茶杯修复分镜。

## 硬：Medium
1. **有参考（B/C）** — 整梯 medium **锁参考**（材质/光影/边缘/色温/BG）。抄纪律不抄 motif。参考写实就跟写实；参考卡通就跟卡通。
2. **零参考（A）默认** — **卡通可爱**（cute cartoon / casual chibi-toy merge 图标：圆润块面、软阴影、饱和友好色、微笑感造型但**道具本身仍无脸**除非 brief 要求）。brief 另写 medium 则以 brief 为准。
3. **Mode A 生成必写 stub（防「口头可爱、画面半写实」）** — 每次 GenerateImage description **必须**包含（可英可中，语义等价即可）：`vinyl toy merge icon` · `chibi proportions` · `soft rounded bevels` · `soft painted shadows` · `NO metal specular` · `NO photoreal` · `NO product photography`。缺任一项视为未按 Mode A 执行。
4. **Mode A EXTRA KEEP（A/B 试词，写在 mandatory stubs 旁）** — 额外织入散文：`squishy chibi mass` · `pastel candy brand glue` · `NO catalog product lighting`。与上条一起织成散文，**禁止**裸 bullet 清单（会印进格子）。
5. **Mode B/C 脸红线（真·B/C 修复）** — 硬锁：`props NO faces` / `NO black-dot eyes on props`（道具无脸、无黑点眼）。可选 polish（非单独修复）：`pastel candy brand glue` · `NO catalog product lighting`。若写 `squishy chibi mass`，**必须**同句配对脸禁；**禁止**声称 EXTRA alone 能修 B/C 脸。
6. **实拍漂移** — 在默认卡通可爱或 stylized 参考下，重扣产品实拍/油光不锈钢 HDR/真实木纹微细节；仅当参考/brief 明确写实才允许写实。Mode A 若 dim1 偏产品目录感 → 整梯重生并加码 stub，不得硬过。

## Stub 织入规则（A/B 试词 KEEP）
可验证 stub 来自失败模式，不是空 masterpiece 形容词。写入 GenerateImage 时**织成散文**，**永不**裸 checklist bullets（会印进 sheet）。Chinese OK for section headers；stub 短语可保留英文试词原文。Mode A：mandatory vinyl/chibi + EXTRA KEEP 三件套。Mode B/C：脸禁是硬修复；candy glue + NO catalog lighting 仅为可选 polish。

## Step 0：Ladder bible
域 · 类 · 品牌胶 · medium 来源（参考锁 / 默认卡通可爱 / brief 覆盖）· **L1…LN 逐级物品名词** + 升级理由 · negatives · 易混档。  
Mode C：写出参考「升级课程」，映射到**新域**物品表。  
**L8 = 最大体量或最多零件**；晚档禁「同一超类微差」。

## Step 1：整梯一次生成
1. Prompt 必须：**exactly N**、**编号列出每个名词**、一句品牌胶、一句 medium（A 默认写清 cute cartoon **+ Mode A stub 全套 + EXTRA KEEP 散文**；B/C 写清 face ban + 可选 candy/NO-catalog polish）、网格锁（等大格、统一 BG、无字无脸）。
2. 多色域用共用点缀品牌胶，勿强行同体色。
3. Mode C 垫参考整梯只锁 medium+网格；NEW family、勿抄参考 motif。
4. 切格；均分出血则连通域重切。
5. **N-count gate**：组件数 ≠ N → 失败重来。
6. 任一格 <9.6 → 优先整梯重生；最多 8 轮。

## Step 2：五维 + 整梯审计
1. 风格与品牌胶（2.5）— 默认卡通可爱时偏写实/产品目录感重扣
2. 升级路径（2.5）— 剪影名词测试
3. 图标完成度（2.0）
4. 红线（1.5）— 含 props NO faces / NO black-dot eyes on props
5. 连续与爬升（1.5）

整梯 OK：**所有格 ≥9.6** 且域/相邻/同族/N-count 通过。

## Step 3：交付
sheet + L01…LN + 每格评分 + 整梯审计 + curriculum。

## 稳定性门
连续 **3 组**不同新域过线才算稳；失败→通用规则写回（禁写死本次道具名）。
