# V8-20 skill v2fix 反推笔记（诚实版）

- 时间：2026-10-26 Asia/Shanghai (UTC+8)
- 对照批：`generated_v8_20_skill/` · mean **9.14** · **4/20** 达标（STOP≥9.50）· 16/20 跑满 8 轮
- 本批：`generated_v8_20_skill_v2fix/` · **PARTIAL**（api.apikey.fan `insufficient_quota` 中途额度用尽）
- 本批已完成：4 bot（2×STOP_DROP + 2×配额中断salvage）· mean(ok) **8.725** · 达标 **0/4** · range 8.13–9.1
- 脚本：`scripts/run_v8_20_skill_converge_v2fix.py`（旧 `run_v8_20_skill_converge.py` 未改）

## 1. 本批相对前次改了什么

| 项 | 前次 skill | v2fix |
|---|---|---|
| pad | 链式 previous（R_n edits from R_{n-1}） | 默认 **ref**（每轮从 style_ref 再 edit）；`--pad {ref,previous,auto}` |
| STOP | total≥9.50 ∧ r≥min_rounds | total≥9.50 ∧ **perspective_anatomy≥8.5** ∧ r≥min_rounds |
| 早停 | 无 | **plateau**（连续 2 轮无新 best）或 **drop≥0.3** → 晋升 best |
| 评分失败 | 灌套话「强化档位意图…体积光」并继续链式 | 重试 1 次；仍失败则 **不改 defects / 不坏 pad** |
| 缺陷回流 | 空白/低维 → 套话体积光；【回流修正】偏长 | 低维映射 anatomy/texture/light 专句；**【回流修正】≤2**；透视最低优先 |
| 配额 | 无特殊处理 | 检测 `insufficient_quota` → 全局 abort（避免连败烧重试） |

## 2. 前次 skill 批的真实瓶颈（数据）

从 `generated_v8_20_skill/gen_manifest.json` 轨迹：

1. **评分失败 → 套话 defects → 坏 pad 链式**  
   例：`v8_bot_02` R2/R5 total=None，defects 变成「强化档位意图、边缘完整与体积光…」，随后分数抖动/下滑。
2. **链式 pad 后期劣化**  
   `v8_bot_26`：R4 best 7.97 → R8 6.70（透视 4.0）；`v8_bot_30`：R5 best 9.55 → R6 7.73。满 8 轮很多是在「烧」已过峰的图。
3. **透视/解剖是硬门槛**  
   多数未达标 bot 的 `perspective_anatomy` 长期在 6.5–8.0；即使总分接近 9.5（如 bot_30=9.55）也常被肢体/持物/接触阴影拖住。
4. **达标的 4 张** 多半靠早期轮次碰巧过线，而非稳定回流策略。

## 3. v2fix 已观察到的信号（样本小，n=4）

| bot | best | anat | stop | 解读 |
|---|---|---|---|---|
| v8_bot_02 low | 8.13 (R1) | 6.75 | STOP_DROP | R2/R3 从 ref 再 edit 继续掉；早停保住 R1，但仍远低于前次链式 best 8.96 |
| v8_bot_04 med | **9.10 (R1)** | **8.5** | STOP_DROP | R1 已很接近 9.50；R2/R3 下滑被 drop 截住。说明 **R1 质量够时 pad=ref+早停是对的** |
| v8_bot_06 high | 8.79 (R3) | 8.0 | salvage | 缓慢爬升中被配额打断；透视未到 8.5 |
| v8_bot_07 recom | 8.88 (R2) | 8.0 | salvage | 同上 |

要点：

- **DROP 早停有效**：避免再生成明显更差的轮次（与前次满 8 轮劣化同构）。
- **纯 pad=ref 并不总优于链式**：low 档 bot_02 本批 R1 弱于前次链式峰值 → 「永远从 ref」会丢掉「在已改进图上微调」的收益。
- **解剖门槛会推迟 STOP**：bot_04 R1=9.1/anat8.5 若只看总分已接近，但未到 9.50；门槛合理，但需要更敢改解剖的回流句，而不是光影套话。

## 4. 剩余瓶颈（按优先级）

1. **API 额度**：本批无法跑完 20；一切均值对比暂不可下结论。  
2. **pad 策略过刚**：`ref` 默认防劣化，但牺牲了「改进后继续磨」；需要 **auto**（升则 chain，降则 reset ref）作主路径。  
3. **R1 提示词天花板**：多数档位若 R1 < 8.5，后续无论 pad 都难稳过 9.50。low/medium 的 compose 仍偏「修瑕」叙事，对 Absolute-5D 的透视/质感权重不够主动。  
4. **回流句仍偏模板**：`DIM_FIX['perspective_anatomy']` 是通用句；缺少按 case（持剑手、落脚屋脊、龙翼根、粉彩手指）的 **slug 特化解剖补丁**。  
5. **STOP 与晋升**：drop=0.3 对 VLM 噪声可能略紧；可改为「相对 best 连续 2 次下降」或「drop≥0.3 且 anat 也降」再停。  
6. **达标定义变严**：+anat≥8.5 会让「总分刷到 9.6 但肢体糊」不再算达标——这是正确产品决策，但会让 reached 计数短期下降，需在 HTML/报告里分列「总分达标」vs「总分+透视达标」。

## 5. 下一步具体改动（Top 3 + 附）

### Fix 1 — 默认改 `--pad auto`（代码）
- 规则：本轮 total ≥ 上轮 ok total → 下轮 pad=本轮图；否则 pad=ref。  
- 评分失败：pad 强制回 ref，defects 保持。  
- 预期：兼得 bot_04 类「R1 已强」的稳定，与 bot_02 前次链式爬升。

### Fix 2 — slug/模块级解剖补丁字典（prompt）
在 `defects_from_dims` 之后，若最低维是 `perspective_anatomy`，追加 1 条 case 补丁（仍总长 ≤2）：
- night_city：`孤侠落脚与屋脊接触阴影、持剑手腕与剑柄连接可读`
- pastel_sketch：`屈膝少女手指/腕关节与衣褶遮挡关系清楚，勿融化`
- sunlit_portrait：`肩颈锁骨与发际衔接，二分光下面部平面分面稳定`
- ishtar_canyon：`龙翼根/腹与桥体承托，旅人尺度与阶梯透视一致`
写入 `scripts/run_v8_20_skill_converge_v2fix.py` 的 `CASE_ANAT_FIX` 即可，无需改 scorer。

### Fix 3 — R1 增强：把透视/接触阴影写进 compose 主链（prompt）
对 non-style_jump，在 `compose_style_first_prompt` 之后、首轮就注入一行弱约束（非回流）：  
`结构底线：主体关节/持物连接清楚；接触阴影与承托可读；禁止肢体融化进道具`  
避免只在 R≥2 才谈解剖。low 档也要，否则 R1 解剖分锁死在 ~6.5–7.5。

### 附（配额与工程）
- 跑前用极短 chat probe 检查额度；`insufficient_quota` 立即停整批并写 `SCORE_SUMMARY.status`。  
- HTML 增加「总分≥9.50」与「总分+anat≥8.5」双计数。  
- Desktop 同步坚持 **单文件 CopyFromBox**（≤~3MB）；禁止整包 tgz。

## 6. 诚实结论

- **逻辑方向对**：禁套话缺陷、早停、解剖门槛、pad 可控 —— 都对准了前次 16/20 空转满轮的病因。  
- **本批未能证明均值提升**：额度中断 + 仅 4 个样本；其中 1 个 R1=9.1 很有希望，1 个 low 弱于前次链式峰值。  
- **且慢把 pad=ref 定为「最佳」**：先用 auto 重跑满 20，再对比 mean / reached / 轮次分布。  
- **要继续**：给 `apikey.fan` 充值或换 key → 同脚本 resume（已跳过完成 bot）→ 再出 HTML 与 Desktop。

