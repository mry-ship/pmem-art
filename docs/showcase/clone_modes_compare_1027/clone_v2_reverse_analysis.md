# clone-v2 反向论证（最新代码跑数 · 2026-10-27）

会话：`clone-v2-a-icon` / `clone-v2-b-{key,ui,char}` · 垫图 `val_heart_ref.png`（道具礼盒 icon）

## 1. 结果总表

| 组 | 轮次 | 终稿分 | ≥9.6 停机 | 结构门 |
|:---|:---:|:---:|:---:|:---|
| Mode A 指南针 | 2 | **9.60** | ✓ | — |
| Mode B UI 弹框 | 1 | **9.62** | ✓ | 空中心 PASS |
| Mode B 钥匙 | 2 | **9.60** | ✓ | R1 即钥匙（非礼盒） |
| Mode B 甜品师 | 2 | **9.58** best | ✗ | 圆头/T-pose/无礼盒头 PASS |

报告：`.memory-art/converge/clone-v2-*_report.md`

---

## 2. 与 fix1027（上一版策略跑数）对比

| 现象 | fix1027 | clone-v2（本趟） |
|:---|:---|:---|
| Key R1 主体 | 整图礼盒 → 构图 4.0 / 8.03 | **R1 即钥匙** → 9.58，无回声 defects |
| Key R2 pad | 曾垫礼盒 R1（旧 pad 逻辑） | R1 结构合格 → **pad=auto→R1** 合理 |
| UI | 1 轮 9.62 空壳 | 1 轮 **9.62** 空壳（稳定复现） |
| 四组全 ≥9.6 | 否（3 组 9.56–9.58） | **3/4 达标**；Char 差 0.02（质感维） |

**可论证结论**：`clone_subject` R1 底线 + prompt 强化后，**Mode B 道具参考不再必然 R1 复印**；与「只修 UI 门禁」相比，Icon 路径证据更强。

---

## 3. 策略层：什么被验证了

### 3.1 UI 弹框母版合同

- `ui.PopupClone` + 空中心成片 → 1 轮停机，与 **ui_shell / 结构门** 设计一致。
- 反向论证：此前翻车（中心礼盒）是 **合同层级 + 无门禁**；在默认 shell + judge 回声词下，**brief 不必堆满关键词也能收敛**（本趟 brief 仍写空内容，但模块默认已兜底）。

### 3.2 Mode B 新题材（Icon）

- generate 日志可见 **clone_subject 结构底线** 注入（英：NEW subject silhouette / NO gift box）。
- R1 未出现「完全抄参考」类 defects → **未触发** echo 压分/veto，符合 fail-closed「无信号则不误杀」。
- 仍靠 **medium 锁 + 显式钥匙 prompt** 才稳定换题材；策略是 **必要非充分**，生图层仍要负向与主体词。

### 3.3 pad=auto

- Key R2：`pad=auto→R1`（9.58 板），非 style_ref 回退 → 说明 **仅回声/构图&lt;6 才禁链** 生效；与 fix1027 Key R1 失败后仍链礼盒板对比，逻辑正确。

### 3.4 Character

- R1/R2 均无礼盒头，结构门 **通过**；未达 9.6 因 **加权差 0.02（质感 9.5）**，非结构翻车。
- 反向论证：结构门与分数门 **应解耦**——本组证明结构 OK 仍可能 best-of 未过线。

---

## 4. 仍暴露的缺口（由本趟数据支撑）

1. **UI R1 未注入 `ui_shell` floor（已定位并修）**：brief 写「**非**奖励插画」时，子串「奖励插画」误触 `_UI_SHELL_CENTER_ART_MARKERS`，`ui_shell_clone_task` 返回 False → 生图 prompt 缺结构底线；成片仍空壳靠 brief 与 judge。**修复**：否定前缀感知匹配（`subject_lexicon._affirmative_ui_center_art_marker`）+ 单测。
2. **Char 9.58**：稳定性门「四组全 ≥9.6」仍 **不成立**（3/4）。
3. **Judge 仍依赖 CLI 五维 + 人工 defects**：无自动视觉「是否礼盒」；若 defects 不写回声，门禁不会替人看图。
4. **0.02 分差 polish**：A/Key 均 2 轮才过线 → medium 加权下 **9.56–9.58 平台区** 仍存在，非结构 bug。

---

## 5. 对 skill 设计的反向归纳

| 原假设 | 本趟支持？ | 修正 |
|:---|:---:|:---|
| 「Clone = 锁风格即可」 | ✗ | 必须 **按类合同**（UI shell / Icon 新主体 / Char 眼语法） |
| 「五维 ≥9.6 = 可交付」 | △ | UI/Icon 需 **结构门**；Char 可结构过、分数不过 |
| 「垫 prop 必复印」 | △ | R1 可出钥匙；需 **floor + prompt + 仍可能多轮 polish** |
| 「warm-start recipe 无害」 | ✓（UI 侧） | 过滤奖励弹窗 recipe 后 UI 仍 1 轮达标 |

---

## 6. 建议下一步（非本文件执行）

- Char 再 1 轮只抬质感 / 或 `--scale low` 看是否更快过 9.6（验证分数门与结构门分离）。
- 补 **UI generate 必打 ui_shell floor** 的日志/单测（与 PopupClone 默认一致）。
- 稳定性门正式定义：**4 组 ≥9.6 且 UI/Icon/Char 结构门全过** → 本趟 **Char 阻稳测**。
