# clone-v3 反向论证（否定前缀修复后重跑 · 2026-10-27）

会话：`clone-v3-a-icon` / `clone-v3-b-{key,ui,char}` · 垫图 `val_heart_ref.png`（道具礼盒 icon）

## 1. 结果总表

| 组 | 轮次 | 终稿 | 分 | ≥9.6 | 结构门 |
|:---|:---:|:---|:---:|:---:|:---|
| Mode A 指南针 | 2 | `assets/icon/compass/clone_v3_a_r2.jpg` | **9.60** | ✓ | — |
| Mode B UI 弹框 | 1 | `assets/ui/popupclone/clone_v3_b_ui_r1.jpg` | **9.62** | ✓ | 空中心 PASS；**prompt 含 9-slice floor** |
| Mode B 钥匙 | 3 | `assets/icon/keyclone/clone_v3_b_key_r3.jpg` | **9.60** | ✓ | R1 即钥匙（非礼盒） |
| Mode B 甜品师 | 4 | `assets/character/pastrychef/clone_v3_b_char_r4.jpg` | **9.58** best | ✗ `STOP_PLATEAU` | 圆头/T-pose/无礼盒头 PASS |

报告：`.memory-art/converge/clone-v3-*_report.md`

稳测「四组全 ≥9.6 + 结构门」：**仍 3/4**。Char 再阻稳测。

---

## 2. 与 clone-v2 对照

| 现象 | clone-v2 | clone-v3（本趟） |
|:---|:---|:---|
| UI R1 prompt 有 `ui_shell` floor | ✗（「非奖励插画」误杀） | **✓ 已写入** `Structure floor: 9-slice popup shell…` |
| UI 成片 | 1 轮 9.62 空壳 | 1 轮 **9.62 空壳**（复现） |
| Key R1 主体 | 钥匙 9.58 | 钥匙 **9.58**，无礼盒回声 |
| Key 过线轮次 | 2 | **3**（R2 同板 9.58，R3 金齿哑光才 9.60） |
| Char | 2 轮 9.58 best | **4 轮平台 9.58**，`STOP_PLATEAU` |
| 四组全 ≥9.6 | 3/4 | **3/4** |

**可论证结论**：上一趟唯一策略 bug（否定词误匹配）在本趟 **被跑数验证修好**。分数格局没有新的结构性翻车。

---

## 3. 策略层：什么被验证了

### 3.1 「非奖励插画」不再关掉 UI 底线

- `clone-v3-b-ui.json` R1 `prompt` 含完整 `9-slice popup shell` 句。
- 同一 brief 在修前 `ui_shell_clone_task=False`、floor 为空；修后为 True。
- 成片空中心 1 轮停机，与 floor + 模块默认空壳 **双保险一致**。

### 3.2 Mode B 新题材（Icon）

- R1 generate 日志 / JSON 均有 `clone_subject` floor（NEW subject / NO gift box）。
- R1 成片是钥匙，不是礼盒 → **回声门未触发**，与 fail-closed 设计一致。
- 过线慢在 **质感 9.5 平台**，不是主体抄参考。

### 3.3 pad=auto

- A/Key/Char 的 R2+ 均 `pad=auto→上一轮`，因结构合格。
- Key R2 几乎同板（仍 9.58）；R3 才把金齿改成哑光软塑胶 → **pad 链会锁 polish，但单点材质指令仍可能抬 0.02**。
- Char R2–R3 垫上轮脸，巩膜/蛋糕几乎不动。
- Char R4 **生图时只垫 style_ref**，但 `converge generate` 仍登记 `pad=auto→R3`：**登记垫图 ≠ 实际生图垫图**。成片眼语法仍未抬。

### 3.4 Character：结构门过、分数门不过

- 四轮均无礼盒头、空手 T-pose、帽徽/胸章/脚边蛋糕。
- 未过线只因 **巩膜月牙偏窄（接近深色圆点）+ 蛋糕偏小** → 质感/透视卡在 9.5。
- `STOP_PLATEAU` 在第 4 轮触发，说明策略层已承认「再叠同一改点无效」。

---

## 4. 仍暴露的缺口（本趟新证据）

1. **Char 眼语法生图层锁死**：brief / floor / next_fix 连续写「巩膜月牙」，四轮像素几乎不变。这不是词表 bug，是 **medium 续画 + 模型默认 Q 版黑豆眼**。策略门禁只能在 defects 写了「黑点瞳」时否决；本趟 defects 写的是「接近深色圆点」，未走 echo veto。
2. **pad 登记与真实垫图可分叉**：R4 人工只垫礼盒，CLI 仍记 pad=上一张。可观测性会误导下一轮「该不该再垫」。
3. **0.02 平台复现**：A 2 轮、Key 3 轮才过；Char 四轮停在 9.58。结构门 ≠ 分数门，与 v2 结论相同。
4. **稳测仍不成立**：3/4。Char 是唯一分数阻点。

---

## 5. 对 skill 设计的反向归纳

| 假设 | 本趟 | 修正 |
|:---|:---:|:---|
| 「非奖励插画」会关掉空壳 floor | ✗（已修） | 否定前缀必须感知；本趟验证 |
| 「floor 写入 = 成片一定换题材」 | △ | Icon/UI 成立；Char 眼语法不成立 |
| 「pad=auto 结构合格就可续画」 | △ | 防回声有效；**尺度/眼型缺陷续画会锁死** |
| 「四组稳测靠再跑就能齐」 | ✗ | Char 四轮平台，再跑同一合同仍 9.58 |

---

## 6. 还要不要改代码

**结构正确性：不用再改。** 本趟没有新的词表/门禁假阴性。

若要动代码，只剩 **可选增强**（不是本趟必做）：

- 角色眼语法：尺度类缺陷时 `pad=auto` 不要链上轮（skill 已写，generate 未执行）。
- generate 日志区分「会话登记垫图」和「实际送进生图器的垫图」。
- 稳测定义维持：4 组 ≥9.6 **且** 结构门全过 → 本趟 **Char 仍阻**。
