# Scale 四档重测清单（现行合同 ≥9.60）

> 目的：用现行 `CONVERGE_SCALE_PROFILES` 重跑 4 案例 × 4 档，验证阶梯合理性与稳定性。  
> 旧会话（`scale_*`）阈值为 **9.50**，且 high 曾 `allow_recompose=True`——**不可直接当作现行证据**。

## 现行合同快照

| 档位 | 停机线 | prompt delta | min_round_leap | 机位/姿态/布局 | 光影大修 | 备注 |
| :--- | :---: | :--- | :---: | :---: | :---: | :--- |
| `low` | ≥9.60 | ≤20% vs **首轮** | +0.12 | ❌ | ❌ | 只修瑕；常需换档或跑满 8 轮 |
| `medium` | ≥9.60 | ≤45% vs 上轮（累计≤60% vs 首轮） | +0.22 | ❌ | ✅ | 默认档 |
| `high` | ≥9.60 | ≤70% vs 上轮（累计≤85% vs 首轮） | +0.30 | ✅ | ✅ | `allow_recompose=False` |
| `recompose` | ≥9.60 | ≤85% vs 上轮（累计≤95% vs 首轮） | +0.30 | ✅ | ✅ | **必须** `--recompose-dir`；leap 对齐 high（正交轴，不倒挂） |

停机条件：加权分 ≥9.60 **且** `defects` 有实质短板描述（禁「无明显硬伤」套话）**且** 物理图闸门通过。

## 案例矩阵

| Case | ref | module | recompose-dir |
| :--- | :--- | :--- | :--- |
| 01 night_city | `comparison/style_refs/style_ref_01_night_city.png` | `scene.celestial_night_city` | 从高空飞檐俯瞰改为底层运河石拱桥与乌篷船低机位仰视全景 |
| 02 sketch | `comparison/style_refs/style_ref_02_pastel_sketch.png` | `character.pastel_sketch_girl` | 从地面坐姿近景改为黄金时刻城市天台铁艺栏杆旁站立远眺夕阳海港全景 |
| 03 portrait | `comparison/style_refs/style_ref_03_sunlit_portrait.png` | `character.sunlit_window_portrait` | 从特写胸像拉远为阳光植物温室画室藤椅中景全景，手捧速写本被绿植雏菊环绕 |
| 04 canyon | `comparison/web_refs/web_ref_01_concept_ishtar.png` | `scene.web_01_vertical_alley` | 从垂直天井俯视改为高空雕花石露台平视跨谷三孔石拱大桥与瀑布群，绿龙翱翔于天际神光中 |

会话 ID：`retest_{NN}_{slug}_{scale}`（例：`retest_01_night_city_low`）。  
出图路径：`comparison/retest/{session}_r{N}.jpg`。

## Brief 模板（把 `>=9.50` 全部改为现行语义，勿写进达标线）

- **low**：锁死原机位/姿态/元素，只修解剖与媒介瑕疵  
- **medium**：保持机位与主体，补侧逆光、空气层次与材质  
- **high**：锁身份与画风；可升级镜头张力与戏剧光影（**不要**整段换成另一机位故事）  
- **recompose**：继承画风与身份，**100%** 执行 `--recompose-dir`

## CLI 模板

```bash
python3 pmem_art.py converge start \
  --session retest_01_night_city_low \
  --module scene.celestial_night_city \
  --scale low \
  --ref-image comparison/style_refs/style_ref_01_night_city.png \
  --brief "锁死飞檐男侠俯瞰万家灯火，精修瓦片与长剑金属反光" \
  --ref-analysis "东方仙侠不夜城：左下飞檐男性持剑侠客背影俯瞰万家灯火楼阁与弯月星穹（身份锁死为男性，禁止改成女侠）"

# recompose 例：追加
#   --scale recompose \
#   --recompose-dir "从高空飞檐俯瞰改为底层运河石拱桥与乌篷船低机位仰视全景"

python3 pmem_art.py converge generate --session <id> --image comparison/retest/<id>_r1.jpg --prompt "..."
python3 pmem_art.py converge judge --session <id> --image comparison/retest/<id>_r1.jpg \
  --dims "构图x/光影x/透视x/质感x/风格x" \
  --defects "……具体部位短板……" \
  --next-fix "……正向修正……"

python3 pmem_art.py converge finish --session <id> --apply   # 达标或满轮后
```

## 验收指标

1. **阶梯**：同案终分是否仍 `low ≤ medium ≤ recompose ≤ high`  
2. **low 达标率**：`passed @9.6` 比例、轮次、是否被迫换档  
3. **high ≠ recompose**：high 是否偷偷做成换机位故事  
4. **recompose 构图维**是否明显高于同案 medium  
5. **稳定性**：同图二次 `judge` 分差；可选独立 VLM 盲评 Δ  
6. **跨案方差**：同档四案终分 σ（旧会话 σ≈0，属异常）

## 旧会话对照（勿混用阈值）

| 档位 | 旧终分范围 (thr=9.5) | 现行 ≥9.6 |
| :--- | :--- | :--- |
| low | 9.54–9.56 | 全挂 |
| medium | 全 9.62 | 过 |
| recompose | 9.63–9.65 | 过 |
| high | 9.79–9.83 | 过 |

## 执行顺序建议

1. **Case 01**：`low` + `high` 对照（验证低档冲线失败 vs 高档可达）  
2. 同案补 `medium` + `recompose`  
3. 再铺 Case 02→04  
4. 汇总写入本文件「重测结果」节，并校正 README / showcase 表述

## 重测结果（进行中）

### Case 01 · night_city（`aspect-ratio=9:16` · **强垫图原图** · 男性浅灰白袍）

`scene.CelestialCity` 主规格 `9:16`（`720x1280` / `405x720`）。四档均挂 `style_ref_01_night_city.png`；失败自由重绘已挪到 `comparison/retest/_bad_free_redraw/`。

| session | 状态 | 轨迹 (R1→R3) | 备注 |
| :--- | :--- | :--- | :--- |
| `retest_01_night_city_low` | → R4 | 8.58 → 8.77 → **8.86** | 贴原图俯瞰浅灰白袍；只修瑕；距 9.6 仍远 |
| `retest_01_night_city_medium` | → R4 | 8.74 → 8.91 → **9.05** | 同构图补轮廓光/雾/材质 |
| `retest_01_night_city_high` | → R4 | 8.87 → 9.12 → **9.30** | 俯瞰内升级飘带剑气瀑布星璇；未改运河 |
| `retest_01_night_city_recompose` | → R4 | 8.69 → 8.91 → **9.07** | 运河石拱桥乌篷船仰视；继承原图色板与男侠 |

阶梯（R3）：`low (8.86) < medium (9.05) ≈ recompose (9.07) < high (9.30)` —— 均未达 9.60。

### 反向分析（强垫图批次 · 2026-10-25）

#### 观测表

| 档 | R1→R3 | 单轮跃升 | prompt Δ（vs 合同基线） | 合同 leap | 实测是否停滞 |
| :--- | :--- | :--- | :--- | :---: | :--- |
| low | 8.58→8.77→8.86 | +0.19 / **+0.09** | 6% / 8%（≤20% ✅） | 0.12 | R3 停滞 |
| medium | 8.74→8.91→9.05 | **+0.17 / +0.14** | 12% / 14%（≤45% ✅） | 0.22 | R2–R3 均停滞 |
| high | 8.87→9.12→9.30 | **+0.25 / +0.18** | 15% / 15%（≤70% ✅） | 0.30 | R2–R3 均停滞 |
| recompose | 8.69→8.91→9.07 | **+0.22 / +0.16** | 17% / 10%（≤85% ✅） | 0.30 | R2–R3 均停滞 |

线性外推到 R8：`low≈9.56（仍可能不达 9.60）`；`medium/high/recompose` 理论上可达。

#### 根因（按优先级）

1. **low 结构性够不到 9.60（产品合同问题，不是偶然）**  
   R3 五维已到「构图/风格 9.0、其余 8.8」，加权仍 8.86。权重 50% 压在透视+质感，又禁止光影大修/换机位——贴原图修瑕时冲击力维抬不上去。旧会话 low「9.54–9.56 达标」依赖旧阈值 9.50 + 模板填分，**不能证明 low@9.60 可达**。

2. **`min_round_leap` 高于真实垫图跃升（软预警失真）**  
   强垫图下相邻轮典型跃升约 `0.14–0.25`，但 medium/high/recompose 合同分别要 `0.22 / 0.30 / 0.30`。结果：从 R2 起几乎轮轮 `stagnated=True`。预警变成噪音，Agent 容易误判「该换档/该大改」，反而破坏 low/medium 合同。

3. **反虚高关键词「数字化」过宽（曾误杀 high）**  
   缺陷写「剑气边缘数字化毛刺」会命中裸词 `数字化` → 硬顶 ≤8.90。真短板是「能量边缘毛刺」，不是「数字化噪点滤镜」。应用更长短语优先（已有 `数字化噪点|痕迹|滤镜`），裸 `数字化` 应降级或删除。

4. **recompose ≈ medium 分，不代表强度阶梯坏了**  
   recompose 是意图轴（换机位），不是比 medium「更强」的强度档。构图权重 30% 会奖励「方向执行到位」，故终分可贴近 medium；与 high 的差距才是强度信号。验收应看：**构图维是否明显高于同案 medium + 机位是否按 `--recompose-dir` 改变**，不要只比总分。

5. **流程债：未强垫图时的自由重绘会污染分档结论**  
   早期批次挂了 `--ref-image` 路径，但出图是同题材重画（青绿绣金封面风）。那批数据已隔离到 `_bad_free_redraw/`。Skill/Agent 门禁应强制：judge 前对照原图检查袍色/机位/身份，漂移则拒收本轮。

#### 建议修复（代码 / 产品）

| # | 动作 | 理由 |
| :---: | :--- | :--- |
| A | **low 停机策略二选一**：降 soft-target（如 9.3）或文档明示「low 常需换 medium/high 冲 9.6」 | 外推 R8 仍可能 <9.60 |
| B | **下调 leap 或改为衰减**：如 low 0.10 / med 0.15 / high·rec 0.20，或随轮次衰减 | 消除假停滞 |
| C | **收紧 `数字化` 匹配**：只保留「数字化噪点/痕迹/滤镜」，去掉裸词 | 避免 high 假封顶 |
| D | **Skill 加「垫图对照清单」**：low/medium 必须报告与原图的袍色/机位/身份三连 | 防自由重绘混进重测 |
| E | **recompose 验收加构图维 Δ** | 正交轴应用正交指标 |

#### 本批评分可信度

- ✅ 阶梯方向与垫图合同一致，跨档区分度正常（非旧 16 组 σ≈0）。  
- ⚠️ 仍为 Agent 自评，缺独立 VLM 盲评；绝对分可能仍偏高 0.3–0.8（参照历史盲评 Δ）。  
- ⚠️ 未跑满 8 轮，A/B 项需 R4–R8 或换档实验再确认。
