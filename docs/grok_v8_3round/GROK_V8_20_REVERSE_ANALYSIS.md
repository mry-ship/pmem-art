# V8-20 Grok GenerateImage 反推分析

- **生成后端**: Cursor `GenerateImage` (Grok)
- **收敛**: v2fix (threshold 9.5, anat gate 7.0, pad=auto, max_rounds 实践=2)
- **打分**: offline Absolute-5D（VLM gpt-6-sol `INSUFFICIENT_BALANCE`）
- **产物目录**: `/workspace/pmem-art-v8/generated_v8_20_skill_grok/`
- **本分析路径**: `/workspace/pmem-art-v8/generated_v8_20_skill_grok/GROK_V8_20_REVERSE_ANALYSIS.md`
- **Showcase**: `pmem_art_images_v8_20bots_grok_showcase.html`（embed 22MB）/ `_desktop.html`（外链）
- **时间**: 2026-10-27 Asia/Shanghai

## 0. Headline vs 对照

| 跑次 | mean_final | n | 备注 |
|---|---:|---:|---|
| **Grok (本跑)** | **8.286** | 20 | min=7.65 max=8.8; 0×≥9.5; stop=practical_stop_offline_ceiling_r2×20 |
| gpt-image (generated_v8_20_skill) | **8.938** | 20 | 对照 mean 用户口径 8.94 |
| oct26 backup | **9.139** | 20 | 用户口径 9.14 |

- **Δ vs gpt-image**: -0.652（约 −0.65）
- **Δ vs backup**: -0.853（约 −0.85）
- **重要 caveat**: 本跑 anatomy 维被 offline scorer 置为 NEUTRAL_PRIOR=7.0（不可验透视/解剖 → N/A），因此总分天花板被系统性压低；与 gpt-image / backup 的 VLM 真分不可直接等价，但相对排序与缺陷模式仍可反推。

## 1. Per-bot 明细

| bot | style/scale | final | bestR | anat | light | tex | style | gpt | Δgpt | stop | R2 effect | top defects |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| v8_bot_02 | night_city/low_best | 7.71 | R2 | 7.00 | 7.10 | 7.59 | 7.78 | 7.96 | -0.25 | practical_stop_r2 | helped R1 7.51→R2 7.71 | perspective_anatomy偏低(7.00); lighting_color偏低(7.10) |
| v8_bot_04 | night_city/medium_best | 8.17 | R1 | 7.00 | 7.10 | 7.59 | 9.32 | 8.45 | -0.28 | practical_stop_r2 | flat (R2≈R1) | perspective_anatomy偏低(7.00); lighting_color偏低(7.10) |
| v8_bot_06 | night_city/high_best | 8.45 | R2 | 7.00 | 9.12 | 7.59 | 9.32 | 8.76 | -0.31 | practical_stop_r2 | helped R1 7.97→R2 8.45 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_07 | night_city/recompose | 8.80 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 9.19 | -0.39 | practical_stop_r2 | hurt R1 8.80→R2 8.56 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_08 | night_city/recompose_bold | 8.48 | R1 | 7.00 | 7.10 | 7.59 | 9.32 | 8.59 | -0.11 | practical_stop_r2 | flat (R2≈R1) | perspective_anatomy偏低(7.00); lighting_color偏低(7.10) |
| v8_bot_10 | pastel_sketch/low_best | 8.22 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 8.81 | -0.59 | practical_stop_r2 | hurt R1 8.22→R2 7.86 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_12 | pastel_sketch/medium_best | 8.63 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 8.6 | +0.03 | practical_stop_r2 | flat (R2≈R1) | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_14 | pastel_sketch/high_best | 8.45 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 9.01 | -0.56 | practical_stop_r2 | hurt R1 8.45→R2 7.94 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_15 | pastel_sketch/recompose | 8.22 | R1 | 7.00 | 9.12 | 6.33 | 8.16 | 9.49 | -1.27 | practical_stop_r2 | flat (R2≈R1) | texture_detail偏低(6.33); perspective_anatomy偏低(7.00) |
| v8_bot_16 | pastel_sketch/recompose_bold | 7.99 | R2 | 7.00 | 7.10 | 9.26 | 7.00 | 9.0 | -1.01 | practical_stop_r2 | helped R1 7.65→R2 7.99 | 与参考规格偏离; perspective_anatomy偏低(7.00) |
| v8_bot_18 | sunlit_portrait/low_best | 8.44 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 9.05 | -0.61 | practical_stop_r2 | hurt R1 8.44→R2 8.08 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_20 | sunlit_portrait/medium_best | 8.49 | R1 | 7.00 | 9.12 | 6.75 | 9.32 | 8.95 | -0.46 | practical_stop_r2 | flat (R2≈R1) | texture_detail偏低(6.75); perspective_anatomy偏低(7.00) |
| v8_bot_22 | sunlit_portrait/high_best | 8.45 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 9.25 | -0.80 | practical_stop_r2 | hurt R1 8.45→R2 8.15 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_23 | sunlit_portrait/recompose | 8.43 | R1 | 7.00 | 9.12 | 7.59 | 8.16 | 9.3 | -0.87 | practical_stop_r2 | flat (R2≈R1) | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_24 | sunlit_portrait/recompose_bold | 7.65 | R1 | 7.00 | 5.00 | 9.26 | 7.00 | 9.49 | -1.84 | practical_stop_r2 | flat (R2≈R1) | 死黑/过曝失控；与参考规格偏离; lighting_color偏低(5.00) |
| v8_bot_26 | ishtar_canyon/low_best | 8.08 | R1 | 7.00 | 9.12 | 6.33 | 9.32 | 8.62 | -0.54 | practical_stop_r2 | flat (R2≈R1) | texture_detail偏低(6.33); perspective_anatomy偏低(7.00) |
| v8_bot_28 | ishtar_canyon/medium_best | 8.63 | R1 | 7.00 | 9.12 | 7.59 | 9.32 | 8.81 | -0.18 | practical_stop_r2 | hurt R1 8.63→R2 8.15 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_30 | ishtar_canyon/high_best | 7.94 | R1 | 7.00 | 9.12 | 6.33 | 8.16 | 8.89 | -0.95 | practical_stop_r2 | flat (R2≈R1) | texture_detail偏低(6.33); perspective_anatomy偏低(7.00) |
| v8_bot_31 | ishtar_canyon/recompose | 8.43 | R1 | 7.00 | 9.12 | 7.59 | 8.16 | 9.49 | -1.06 | practical_stop_r2 | hurt R1 8.43→R2 8.22 keep R1 | perspective_anatomy偏低(7.00); texture_detail偏低(7.59) |
| v8_bot_32 | ishtar_canyon/recompose_bold | 8.05 | R1 | 7.00 | 9.12 | 7.59 | 7.00 | 9.04 | -0.99 | practical_stop_r2 | flat (R2≈R1) | 与参考规格偏离; perspective_anatomy偏低(7.00) |

### 1.1 Anatomy / stop / rounds 摘要
- **anatomy**: 全员 `perspective_anatomy=7.00`（offline NEUTRAL_PRIOR）。不是真解剖分，而是 scorer 不可验 → 全 N/A。
- **stop reason**: 全员 `practical_stop_offline_ceiling_r2` —— offline 几乎不可能摸到 9.6，故 R2 后强制停（契约 max 8，实践 max 2）。
- **R2 helped (3)**: 02(+0.20), 06(+0.48), 16(+0.34) —— 低开局/风格弱者 refinement 有用。
- **R2 hurt (7, best 仍取 R1)**: 07/10/14/18/22/28/31 —— 高开局被 pad-from-previous 或 defect reflow 拉歪；promote-best-of 救回。
- **R2 flat (10)**: 同分或近似 —— 收敛信号弱 / 同构图复刻。

## 2. 跨 20 模式：Grok vs gpt-image

### 2.1 Style / scale 均值

| 切片 | Grok mean | gpt mean | Δ |
|---|---:|---:|---:|
| style:night_city | 8.322 | 8.590 | -0.268 |
| style:pastel_sketch | 8.302 | 8.982 | -0.680 |
| style:sunlit_portrait | 8.292 | 9.208 | -0.916 |
| style:ishtar_canyon | 8.226 | 8.970 | -0.744 |
| scale:low_best | 8.113 | 8.610 | -0.497 |
| scale:medium_best | 8.480 | 8.703 | -0.223 |
| scale:high_best | 8.322 | 8.977 | -0.655 |
| scale:recompose | 8.470 | 9.367 | -0.897 |
| scale:recompose_bold | 8.043 | 9.030 | -0.987 |

**系统性弱势**:
- `recompose_bold`（Grok 8.04 vs gpt 9.03, Δ≈−1.0）与 `recompose`（8.47 vs 9.44, Δ≈−1.0）—— 大胆重构图在 Grok+弱参考强度下最伤。
- `sunlit_portrait` / `pastel_sketch` 的高 gpt 分案例落差最大（24/15/23）。
- `night_city` 相对最抗跌（Δ≈−0.3），尤其 medium/recompose_bold。
- `medium_best` 是 Grok 相对最稳的 scale（8.48, Δ≈−0.2）。
- `low_best` 两边都偏低，但 Grok 更低（8.11 vs 8.61）。

### 2.2 五维均值差距（Grok offline vs gpt 跑 vlm_scores 聚合）

| dim | Grok offline mean | gpt-skill vlm pool | backup pool | 解读 |
|---|---:|---:|---:|---|
| composition | 9.20 | 9.08 | 9.69 | Grok 构图仍强；非主因 |
| lighting_color | 8.51 | 8.22 | 9.02 | 均值不差，但尾部 24=5.0 / 若干 7.1 拖累 |
| **perspective_anatomy** | **7.00** | **7.71** | **8.22** | **最大系统性缺口（评分器 + 可能真弱点）** |
| texture_detail | 7.53 | 7.98 | 8.29 | Grok 质感偏糊/欠细节，14/20 报偏低 |
| spec_style | 8.66 | 8.93 | 9.51 | 风格锁尚可；bold/recompose 掉到 7.0 |

### 2.3 Defect 频率（best round）
- `perspective_anatomy偏低` ×20（全员，含先验）
- `texture_detail偏低` ×14
- `lighting_color偏低` ×4（02/04/08/16 等）
- `spec_style偏低` / 规格偏离 ×少数（16/24/32 bold 族）

## 3. 可调杠杆（按期望收益排序）

| 秩 | 杠杆 | 期望增益 | 建议动作 |
|---:|---|---|---|
| 1 | **恢复真 VLM 打分**（gpt-6-sol / 等价） | +0.4～0.8 mean 观感对齐 + 可冲 9.5 | 充值/换 key；否则 offline 天花板使 converge 信号失真 |
| 2 | **pad policy: 优先 pad=ref（非 previous）** 当 R1≥8.2 | +0.2～0.4 on hurt 组 | R2 hurt 7 例多为 pad-from-previous 漂移；高开局锁 ref |
| 3 | **recompose / bold 提示词降激进** | +0.5～1.0 on 15/16/23/24/31/32 | 去掉“bold recompose / extreme FOV”类；改为 mild crop + 同镜头 |
| 4 | **解剖/手/脸硬约束写入 prompt** | +anat 真分（VLM 后可见） | 每轮强制：`correct human anatomy, five fingers, coherent joints, no warped limbs`；portrait 加 iris/双层眼 |
| 5 | **texture / micro-detail 指令** | +0.2～0.4 texture | `fine grain fabric weave, pore-level skin, crisp specular edges`；避免 over-smooth |
| 6 | **reference strength 措辞** | +style 锁 | GenerateImage 多图时：`match style_ref lighting palette and medium exactly; treat refs as hard constraints` |
| 7 | **early-stop / max_rounds** | 省成本；Hurt 组避免 R2 | 若 R1≥8.5 且 anat_gate ok → stop；实践上 Grok 可先 max_rounds=1 再定点 R2 |
| 8 | **defect reflow 措辞** | 中 | 只改被点名维；禁止“reimagine / redesign composition” |
| 9 | **per-case structure floors** | 中 | portrait/ishtar: anat floor 真 VLM≥7.5 才晋级；offline 阶段改用 composition+style 代理门 |
| 10 | **aspect ratio** | 小～中 | 保持与 gpt 跑一致；勿在 Grok 上换 AR 做无关变量 |
| 11 | **concurrency/batch** | 未见证据** | 本跑 concurrency=4，无 batch 间质量相关异常；保持 4 |

## 4. Do-next patch list

### 4.1 先重跑（按 Δgpt 最差 / 可修）
1. **v8_bot_24** sunlit recompose_bold (7.65, Δ−1.84) — lighting=5.0 / style=7.0
2. **v8_bot_15** pastel recompose (8.22, Δ−1.27) — texture=6.33
3. **v8_bot_31** ishtar recompose (8.43, Δ−1.06)
4. **v8_bot_16** pastel recompose_bold (7.99, Δ−1.01)
5. **v8_bot_32** ishtar recompose_bold (8.05, Δ−0.99)
6. **v8_bot_30** ishtar high (7.94, Δ−0.95) — texture=6.33
7. **v8_bot_23** sunlit recompose (8.43, Δ−0.87)
8. **v8_bot_02** night low (7.71) — 虽 Δ 小但绝对分最低梯队，R2 已帮助，可再 R3-with-ref

### 4.2 确切 prompt/policy 变更（试）
- `run_v8_20_skill_converge_grok.py` / v2fix policy:
  - `pad_mode`: `auto` → **`ref_if_score_ge_8.2 else auto`**
  - `max_rounds` 实践: 保持 2，但加 **`early_stop_if_r1 >= 8.5`**
  - recompose_bold bots: 换 **mild_recompose** 模板（禁止 extreme angle / redesign）
  - 全局 append: anatomy lock + texture micro-detail + `match style_ref exactly`
- defect reflow: 模板改为 `fix ONLY: {defect_dims}. Keep identical composition, camera, pose, crop.`
- 评分: 优先恢复 VLM；offline 时 **不要** 用 anat_gate=7.0 作为晋级依据（改 composition≥9.0 & style≥8.5）

### 4.3 不要改
- **不要** 为冲分改 aspect ratio / 换 style_ref 图（对照会毁）
- **不要** 关掉 promote-best-of（R2 hurt 全靠它）
- **不要** 把 concurrency 提到 >4 当唯一优化（无证据）
- **不要** 在 VLM 余额恢复前宣称“Grok 打不过 9.6”——那是 scorer 天花板，不是生成器终局
- **不要** 删 gpt Desktop 集；对照需要并存
- **不要** 把 offline 的 anat=7.0 解读成“Grok 全员解剖失败”而不开 VLM 复核

## 5. 对照结论

| | Grok | gpt-image | backup |
|---|---:|---:|---:|
| mean | **8.286** | **8.94** | **9.14** |
| ≥9.5 | 0/20 | (gpt 跑有) | (backup 有) |
| 主瓶颈 | offline anat 先验 + texture + bold/recompose | — | — |

**一句话**: Grok 本跑比 gpt-image 低约 **0.65**、比 backup 低约 **0.85**；一半落差来自 **offline anatomy=7.0 天花板** 与 **recompose/bold 策略不适配**，另一半来自 **texture 偏弱** 与 **R2 pad-previous 伤害高开局**。下一刀：恢复 VLM + pad=ref for high R1 + 软化 bold/recompose，优先重跑 24/15/31/16/32/30/23/02。

## 附录 · 路径

- Out: `/workspace/pmem-art-v8/generated_v8_20_skill_grok/`
- Manifest: `gen_manifest.json`
- Scores: `vlm_scores.json` / `showcase_scores.json` / `SCORE_SUMMARY.json`
- Showcase embed: `pmem_art_images_v8_20bots_grok_showcase.html`
- Showcase desktop: `pmem_art_images_v8_20bots_grok_showcase_desktop.html`
- 本文件: `GROK_V8_20_REVERSE_ANALYSIS.md`
- Desktop 目标: `/Users/yanghu/Desktop/pmem-art/`（main showcase → Grok；保留 `generated_v8_20_skill/` gpt 集）
