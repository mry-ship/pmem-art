# V3 / V6 Showcase · Offline Absolute-5D vs VLM（gpt-6-sol）结论

数据源：
- `pmem_art_images_v3_16bots_showcase.html`（Desktop）→ 20 唯一图（近全分辨率）
- `pmem_art_images_v6_32bots_showcase.html` → 36 唯一图（**HTML 内嵌半分辨率缩略图 202–360px**）
- 明细：`/Users/yanghu/Desktop/pmem-art-images/v3_showcase_dual_a5d.{json,md}`、`v6_showcase_dual_a5d.{json,md}`

## 总表

| set | n | mean offline | mean VLM | MAE | bias (off−vlm) | \|Δ\|≤1 |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| v3 | 20/20 | 8.39 | 8.00 | 0.40 | +0.39 | 19/20 |
| v6 | 36/36 | 7.90 | 7.46 | 0.47 | +0.44 | 32/36 |

## 问题与解释

1. **V6 只有缩略图**  
   Showcase HTML 嵌入 JPEG 约 13KB、宽 202–360px，无磁盘原图可替代。离线 `spec_style`/纹理代理与 VLM 都会被分辨率拖低；同款 style_ref 在 v3 全图 VLM≈7.75，在 v6 缩略 VLM≈6.49。**跨 showcases 的绝对分不可直接横比。**

2. **离线系统性偏高约 +0.4**  
   与 v9.1 在 V7 上的 MAE≈0.5 一致。主因：`perspective_anatomy` 整批填 **NEUTRAL_PRIOR=7.0**（无可靠代理），pastel 类构图/质感代理偏乐观（v3 pastel bias≈+0.74，v6≈+0.77）。

3. **离线区分度不足**  
   大量 bot 锁在 8.10 / 8.24 / 8.59 等离散档；VLM 同 case 内拉开约 0.5–1.5。离线适合门槛/无 Key 兜底，不适合细排行。

4. **VLM（内容结论，以近全分辨率 v3 为准）**  
   - night_city / ishtar：16 bot 全部高于原图；recompose / high 更稳。  
   - pastel：bot 均高于弱原图（ref 7.07），但绝对分仍偏低（7.4–8.1）。  
   - sunlit：仅 recompose 明显赢原图（8.42 vs 8.19）；多数 high/low 略低于原图。  
   - v6 缩略上 night_city 提升最大（ref 6.49 → bold 7.88），但绝对天花板受分辨率限制。

## 结论

- **双轨对齐（度量）**：配对 MAE≈0.4–0.5；离线系统性偏高 ~0.4，pastel/解剖更宽。  
- **收敛闸门**：无 Key **不要**用离线 STOP=8.50（假早停）。改为本模型按 Absolute-5D 检查表评分，门槛仍 9.5；满轮 best-of-N。像素尺仅旁证。  
- **V6 结论要降权**：showcase 缩略图；严肃对比需全分辨率。  
- **生成侧**：v3 night/ishtar 超原图较稳；sunlit/pastel 仍弱。
